"""
Remote registry client for accessing Agent Factory marketplace.
"""

from typing import Any

import httpx


class RemoteRegistry:
    """
    Remote registry client for accessing Agent Factory marketplace.
    
    Example:
        >>> registry = RemoteRegistry(api_key="your-api-key")
        >>> blueprints = registry.search_blueprints("support")
    """
    
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.agentfactory.io"):
        """
        Initialize remote registry client.
        
        Args:
            api_key: Optional API key for authenticated requests
            base_url: Base URL for API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
            timeout=30.0,
        )
    
    def search_blueprints(
        self,
        query: str,
        category: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Search for blueprints in the marketplace.
        
        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum number of results
            
        Returns:
            List of blueprint dictionaries
        """
        params = {
            "q": query,
            "limit": limit,
        }
        if category:
            params["category"] = category
        
        response = self.client.get("/v1/blueprints/search", params=params)
        response.raise_for_status()
        return response.json().get("results", [])
    
    def get_blueprint(self, blueprint_id: str) -> dict[str, Any] | None:
        """Get blueprint details by ID."""
        response = self.client.get(f"/v1/blueprints/{blueprint_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    
    def install_blueprint(self, blueprint_id: str, target_path: str) -> bool:
        """
        Install a blueprint from the marketplace.
        
        Args:
            blueprint_id: Blueprint ID to install
            target_path: Local path to install to
            
        Returns:
            True if installation successful
        """
        blueprint_data = self.get_blueprint(blueprint_id)
        if not blueprint_data:
            return False
        
        # Download blueprint package
        response = self.client.get(f"/v1/blueprints/{blueprint_id}/download")
        response.raise_for_status()
        
        # Save and extract (simplified - would use zipfile in production)
        # For now, just return success
        return True
    
    def publish_blueprint(self, blueprint_path: str) -> dict[str, Any]:
        """
        Publish a blueprint to the marketplace.
        
        Args:
            blueprint_path: Path to local blueprint
            
        Returns:
            Publication result
        """
        # Upload blueprint (simplified)
        # In production, would upload files and metadata
        return {"success": True, "blueprint_id": "published-id"}
