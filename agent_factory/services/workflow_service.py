"""
Workflow service - Business logic for workflow operations.
"""

from typing import Any

from agent_factory.registry.local_registry import LocalRegistry
from agent_factory.runtime.engine import RuntimeEngine
from agent_factory.workflows.model import Workflow


class WorkflowService:
    """Service for workflow operations."""

    def __init__(self, registry: LocalRegistry | None = None, runtime: RuntimeEngine | None = None):
        """
        Initialize workflow service.

        Args:
            registry: Registry instance (optional)
            runtime: Runtime engine instance (optional)
        """
        self.registry = registry or LocalRegistry()
        self.runtime = runtime or RuntimeEngine()

    def create_workflow(self, workflow_data: dict[str, Any]) -> Workflow:
        """
        Create a new workflow.

        Args:
            workflow_data: Workflow data dictionary

        Returns:
            Created workflow
        """
        workflow = Workflow.from_dict(workflow_data)
        self.registry.register_workflow(workflow)
        self.runtime.register_workflow(workflow)
        return workflow

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        """
        Get workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow if found, None otherwise
        """
        return self.registry.get_workflow(workflow_id)

    def list_workflows(self, tenant_id: str | None = None) -> list[str]:
        """
        List all workflow IDs.

        Args:
            tenant_id: Optional tenant ID filter

        Returns:
            List of workflow IDs
        """
        return self.registry.list_workflows()

    def update_workflow(self, workflow_id: str, updates: dict[str, Any]) -> Workflow | None:
        """
        Update a workflow.

        Args:
            workflow_id: Workflow ID
            updates: Dictionary of updates

        Returns:
            Updated workflow if found, None otherwise
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)

        self.registry.register_workflow(workflow)
        self.runtime.register_workflow(workflow)

        return workflow

    def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            True if deleted, False if not found
        """
        return self.registry.delete_workflow(workflow_id)

    def run_workflow(self, workflow_id: str, context: dict[str, Any]) -> str:
        """
        Run a workflow.

        Args:
            workflow_id: Workflow ID
            context: Initial context

        Returns:
            Execution ID
        """
        # Ensure workflow is registered in runtime
        workflow = self.get_workflow(workflow_id)
        if workflow:
            self.runtime.register_workflow(workflow)

        return self.runtime.run_workflow(workflow_id, context)
