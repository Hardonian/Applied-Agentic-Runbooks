"""
Execution service - Business logic for execution operations.
"""

from agent_factory.runtime.engine import Execution, RuntimeEngine


class ExecutionService:
    """Service for execution operations."""
    
    def __init__(self, runtime: RuntimeEngine | None = None):
        """
        Initialize execution service.
        
        Args:
            runtime: Runtime engine instance (optional)
        """
        self.runtime = runtime or RuntimeEngine()
    
    def get_execution(self, execution_id: str) -> Execution | None:
        """
        Get execution by ID.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution if found, None otherwise
        """
        return self.runtime.get_execution(execution_id)
    
    def list_executions(
        self,
        entity_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Execution]:
        """
        List executions with filters.
        
        Args:
            entity_id: Filter by entity ID
            status: Filter by status
            limit: Maximum number of results
            
        Returns:
            List of executions
        """
        return self.runtime.list_executions(entity_id=entity_id, status=status, limit=limit)
    
    def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel an execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            True if cancelled, False if not found or cannot be cancelled
        """
        execution = self.get_execution(execution_id)
        if not execution:
            return False
        
        if execution.status == "running":
            execution.status = "cancelled"
            return True
        
        return False
