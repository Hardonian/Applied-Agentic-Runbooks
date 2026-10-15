"""Input/output sanitization."""

import html
import re
from typing import Any


def sanitize_input(text: str, allow_html: bool = False) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        text: Input text
        allow_html: Whether to allow HTML tags
        
    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return str(text)
    
    # Remove null bytes
    text = text.replace("\x00", "")
    
    # Escape HTML if not allowed
    if not allow_html:
        text = html.escape(text)
    
    # Remove SQL injection patterns (basic)
    sql_patterns = [
        r"(?i)(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(?i)(--|/\*|\*/|;|')",
    ]
    
    for pattern in sql_patterns:
        text = re.sub(pattern, "", text)
    
    # Remove script tags
    text = re.sub(r"(?is)<script\b[^>]*>.*?</script>", "", text)
    
    return text.strip()


def sanitize_output(data: Any) -> Any:
    """
    Sanitize output data.
    
    Args:
        data: Output data
        
    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        return sanitize_input(data, allow_html=False)
    elif isinstance(data, dict):
        return {k: sanitize_output(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_output(item) for item in data]
    else:
        return data
