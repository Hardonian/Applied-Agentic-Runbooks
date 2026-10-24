"""
Runtime engine for executing agents and workflows with prompt logging.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from agent_factory.agents.agent import Agent, AgentResult
from agent_factory.promptlog.model import Run as RunModel
from agent_factory.promptlog.storage import PromptLogStorage, SQLiteStorage
from agent_factory.telemetry.collector import get_collector
from agent_factory.telemetry.model import UserActivatedEvent, UserSignupEvent
from agent_factory.workflows.model import Workflow, WorkflowResult


@dataclass
class Execution:
    """Represents an execution instance."""
    id: str
    type: str  # "agent" or "workflow"
    entity_id: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None
    result: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class RuntimeEngine:
    """
    Runtime engine for executing agents and workflows with integrated prompt logging.
    
    Example:
        >>> engine = RuntimeEngine()
        >>> engine.register_agent(agent)
        >>> result = engine.run_agent(agent.id, "Hello")
    """
    
    def __init__(
        self,
        prompt_log_storage: PromptLogStorage | None = None,
        tenant_id: str | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
    ):
        """
        Initialize runtime engine.
        
        Args:
            prompt_log_storage: Optional prompt log storage for logging runs
            tenant_id: Optional tenant ID for telemetry
            user_id: Optional user ID for telemetry
            project_id: Optional project ID for telemetry
        """
        self.executions: dict[str, Execution] = {}
        self.agents_registry: dict[str, Agent] = {}
        self.workflows_registry: dict[str, Workflow] = {}
        self.prompt_log_storage = prompt_log_storage or SQLiteStorage()
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.project_id = project_id
        self.telemetry_collector = get_collector()
    
    def register_agent(self, agent: Agent) -> None:
        """Register an agent in the runtime."""
        self.agents_registry[agent.id] = agent
        # Wire prompt logging into agent
        if not agent.prompt_log_storage:
            agent.prompt_log_storage = self.prompt_log_storage
    
    def register_workflow(self, workflow: Workflow) -> None:
        """Register a workflow in the runtime."""
        # Workflows loaded from the persistent registry already carry the
        # agents they reference.  Preserve those bindings when adding the
        # workflow to a fresh runtime (for example after an API restart).
        self.agents_registry.update(workflow.agents_registry)
        self.workflows_registry[workflow.id] = workflow
        # Keep a shared registry so agents registered after the workflow are
        # immediately available to it as well.
        workflow.agents_registry = self.agents_registry
    
    def run_agent(
        self,
        agent_id: str,
        input_text: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Run an agent and return execution ID.
        
        Args:
            agent_id: Agent ID to run
            input_text: Input text
            session_id: Optional session ID
            context: Optional context
            
        Returns:
            Execution ID
        """
        agent = self.agents_registry.get(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        execution_id = str(uuid.uuid4())
        
        # Track user activation (first agent run)
        if self.user_id:
            self._track_activation_if_first_run(agent_id)
        execution = Execution(
            id=execution_id,
            type="agent",
            entity_id=agent_id,
            status="running",
            created_at=datetime.now(),
            metadata={"input_text": input_text, "session_id": session_id, "context": context},
        )
        self.executions[execution_id] = execution
        
        try:
            result = agent.run(input_text, session_id=session_id, context=context)
            
            execution.status = "completed"
            execution.completed_at = datetime.now()
            execution.result = result
            
            # Log to prompt log (agent already logs internally, but we log execution too)
            self._log_execution(execution_id, agent_id, input_text, result)
            
            # Record telemetry
            self.telemetry_collector.record_agent_run(
                agent_id=agent_id,
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                project_id=self.project_id,
                agent_name=getattr(agent, "name", None),
                session_id=session_id,
                status="completed" if execution.status == "completed" else "failed",
                execution_time=result.execution_time if result else 0.0,
                tokens_used=result.tokens_used if result else 0,
                cost_estimate=getattr(result, "cost_estimate", 0.0) if result else 0.0,
                input_length=len(input_text),
                output_length=len(result.output) if result and result.output else 0,
            )
            
            return execution_id
            
        except Exception as e:
            execution.status = "error"
            execution.completed_at = datetime.now()
            execution.error = str(e)
            raise
    
    def run_workflow(
        self,
        workflow_id: str,
        context: dict[str, Any],
        start_step: str | None = None,
    ) -> str:
        """
        Run a workflow and return execution ID.
        
        Args:
            workflow_id: Workflow ID to run
            context: Initial context
            start_step: Optional step ID from which execution should begin
            
        Returns:
            Execution ID
        """
        workflow = self.workflows_registry.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        if start_step and start_step not in {step.id for step in workflow.steps}:
            raise ValueError(f"Workflow step not found: {start_step}")
        
        execution_id = str(uuid.uuid4())
        execution = Execution(
            id=execution_id,
            type="workflow",
            entity_id=workflow_id,
            status="running",
            created_at=datetime.now(),
            metadata={"context": context, "start_step": start_step},
        )
        self.executions[execution_id] = execution
        
        try:
            result = workflow.execute(context, start_step=start_step)
            
            execution.status = "completed"
            execution.completed_at = datetime.now()
            execution.result = result
            
            # Log workflow execution
            self._log_workflow_execution(execution_id, workflow_id, context, result)
            
            # Record telemetry
            workflow = self.workflows_registry.get(workflow_id)
            self.telemetry_collector.record_workflow_run(
                workflow_id=workflow_id,
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                project_id=self.project_id,
                workflow_name=getattr(workflow, "name", None) if workflow else None,
                status="completed" if execution.status == "completed" else "failed",
                execution_time=result.execution_time if result else 0.0,
                steps_completed=getattr(result, "steps_completed", 0) if result else 0,
                steps_total=getattr(result, "steps_total", 0) if result else 0,
                tokens_used=getattr(result, "tokens_used", 0) if result else 0,
                cost_estimate=getattr(result, "cost_estimate", 0.0) if result else 0.0,
            )
            
            return execution_id
            
        except Exception as e:
            execution.status = "error"
            execution.completed_at = datetime.now()
            execution.error = str(e)
            raise
    
    def _log_execution(
        self,
        execution_id: str,
        agent_id: str,
        input_text: str,
        result: AgentResult,
    ) -> None:
        """Log agent execution to prompt log."""
        try:
            run = RunModel(
                run_id=execution_id,
                agent_id=agent_id,
                inputs={"input": input_text},
                outputs={"output": result.output},
                status="success" if result.status.value == "completed" else "error",
                execution_time=result.execution_time,
                tokens_used=result.tokens_used,
                cost_estimate=0.0,
            )
            self.prompt_log_storage.save_run(run)
        except Exception:  # nosec B110 -- prompt-log persistence is best-effort and must not fail an execution
            pass
    
    def _log_workflow_execution(
        self,
        execution_id: str,
        workflow_id: str,
        context: dict[str, Any],
        result: WorkflowResult,
    ) -> None:
        """Log workflow execution to prompt log."""
        try:
            run = RunModel(
                run_id=execution_id,
                workflow_id=workflow_id,
                inputs=context,
                outputs=result.output,
                status="success" if result.success else "error",
                execution_time=result.execution_time,
                tokens_used=0,
                cost_estimate=0.0,
            )
            self.prompt_log_storage.save_run(run)
        except Exception:  # nosec B110 -- prompt-log persistence is best-effort and must not fail an execution
            pass
    
    def _track_activation_if_first_run(self, agent_id: str) -> None:
        """
        Track user activation if this is their first agent run.
        
        Args:
            agent_id: Agent ID that was run
        """
        if not self.user_id:
            return
        
        try:
            # Check if user has run any agent before
            events = self.telemetry_collector.query_events(
                user_id=self.user_id,
                limit=1000,
            )
            
            # Check if user has activated before
            has_activated = any(
                isinstance(e, UserActivatedEvent) for e in events
            )
            
            if not has_activated:
                # This is first agent run - track activation
                # Get signup date to calculate days to activation
                signup_events = [
                    e for e in events
                    if isinstance(e, UserSignupEvent) or (
                        hasattr(e, 'event_type') and 
                        e.event_type.value in ['tenant_created', 'user_signup']
                    )
                ]
                
                days_to_activation = None
                if signup_events:
                    signup_date = signup_events[0].timestamp
                    days_to_activation = (datetime.utcnow() - signup_date).days
                
                activation_event = UserActivatedEvent(
                    event_id=str(uuid.uuid4()),
                    activation_criteria="first_agent_run",
                    days_to_activation=days_to_activation,
                    tenant_id=self.tenant_id,
                    user_id=self.user_id,
                    project_id=self.project_id,
                )
                
                self.telemetry_collector.record_event(activation_event)
        except Exception:  # nosec B110 -- activation telemetry is best-effort (comment: tracking failure must not fail execution)
            # Don't fail execution if activation tracking fails
            pass
    
    def get_execution(self, execution_id: str) -> Execution | None:
        """Get execution by ID."""
        return self.executions.get(execution_id)
    
    def list_executions(
        self,
        entity_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Execution]:
        """
        List executions with optional filters.
        
        Args:
            entity_id: Filter by entity ID
            status: Filter by status
            limit: Maximum number of results
            
        Returns:
            List of executions
        """
        results = list(self.executions.values())
        
        if entity_id:
            results = [e for e in results if e.entity_id == entity_id]
        
        if status:
            results = [e for e in results if e.status == status]
        
        results.sort(key=lambda e: e.created_at, reverse=True)
        
        return results[:limit]
