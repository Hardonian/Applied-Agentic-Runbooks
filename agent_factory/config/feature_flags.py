"""Feature flag system for Agent Factory."""

import os


class FeatureFlags:
    """Feature flag manager."""
    
    # Feature flag definitions
    FLAGS = {
        "blueprint_marketplace": {
            "env_var": "FEATURE_BLUEPRINT_MARKETPLACE",
            "default": True,
            "description": "Enable blueprint marketplace functionality"
        },
        "billing": {
            "env_var": "FEATURE_BILLING",
            "default": True,
            "description": "Enable billing and subscription features"
        },
        "multi_tenant": {
            "env_var": "FEATURE_MULTI_TENANT",
            "default": True,
            "description": "Enable multi-tenant features"
        },
        "experiments": {
            "env_var": "FEATURE_EXPERIMENTS",
            "default": False,
            "description": "Enable research experiments feature"
        },
        "advanced_analytics": {
            "env_var": "FEATURE_ADVANCED_ANALYTICS",
            "default": False,
            "description": "Enable advanced analytics and reporting"
        },
        "webhooks": {
            "env_var": "FEATURE_WEBHOOKS",
            "default": True,
            "description": "Enable webhook functionality"
        },
        "sso": {
            "env_var": "FEATURE_SSO",
            "default": False,
            "description": "Enable SSO authentication"
        },
    }
    
    @classmethod
    def is_enabled(cls, flag_name: str, default: bool | None = None) -> bool:
        """
        Check if a feature flag is enabled.
        
        Args:
            flag_name: Name of the feature flag
            default: Default value if flag not found (uses flag definition default)
            
        Returns:
            True if feature is enabled, False otherwise
        """
        if flag_name not in cls.FLAGS:
            if default is not None:
                return default
            return False
        
        flag_def = cls.FLAGS[flag_name]
        env_var = str(flag_def["env_var"])
        default_value = flag_def["default"]
        
        # Check environment variable
        env_value = os.getenv(env_var)
        if env_value is not None:
            return env_value.lower() in ("true", "1", "yes", "on")
        
        # Use default from definition or provided default
        return default if default is not None else bool(default_value)
    
    @classmethod
    def get_all_flags(cls) -> dict[str, bool]:
        """
        Get all feature flags and their current values.
        
        Returns:
            Dictionary mapping flag names to enabled status
        """
        return {
            flag_name: cls.is_enabled(flag_name)
            for flag_name in cls.FLAGS
        }
    
    @classmethod
    def get_flag_info(cls, flag_name: str) -> dict | None:
        """
        Get information about a feature flag.
        
        Args:
            flag_name: Name of the feature flag
            
        Returns:
            Flag information dictionary or None if not found
        """
        if flag_name not in cls.FLAGS:
            return None
        
        flag_def = cls.FLAGS[flag_name].copy()
        flag_def["enabled"] = cls.is_enabled(flag_name)
        return flag_def


# Convenience functions
def is_feature_enabled(flag_name: str, default: bool | None = None) -> bool:
    """
    Check if a feature flag is enabled.
    
    Args:
        flag_name: Name of the feature flag
        default: Default value if flag not found
        
    Returns:
        True if feature is enabled, False otherwise
    """
    return FeatureFlags.is_enabled(flag_name, default)


def get_all_features() -> dict[str, bool]:
    """
    Get all feature flags and their current values.
    
    Returns:
        Dictionary mapping flag names to enabled status
    """
    return FeatureFlags.get_all_flags()


# Common feature flag checks
def blueprint_marketplace_enabled() -> bool:
    """Check if blueprint marketplace is enabled."""
    return is_feature_enabled("blueprint_marketplace")


def billing_enabled() -> bool:
    """Check if billing is enabled."""
    return is_feature_enabled("billing")


def multi_tenant_enabled() -> bool:
    """Check if multi-tenant features are enabled."""
    return is_feature_enabled("multi_tenant")


def experiments_enabled() -> bool:
    """Check if experiments feature is enabled."""
    return is_feature_enabled("experiments")
