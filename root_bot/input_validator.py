import re
from typing import Dict, Any, Optional

class InputValidator:
    """Validates and sanitizes input for the RootBot"""
    
    # Regex patterns for common input types
    PATTERNS = {
        'command': r'^[a-zA-Z0-9_-]+$',  # Alphanumeric, underscore, hyphen
        'filepath': r'^[a-zA-Z0-9/_.-]+$',  # Valid file path characters
        'memory_type': r'^[a-zA-Z0-9_]+$',  # Memory entry type format
        'config_key': r'^[A-Z][A-Z0-9_]*$',  # Config key format (uppercase)
    }

    @classmethod
    def validate_pattern(cls, input_str: str, pattern_name: str) -> bool:
        """Validate input string against a predefined pattern"""
        if pattern_name not in cls.PATTERNS:
            raise ValueError(f"Unknown pattern: {pattern_name}")
        return bool(re.match(cls.PATTERNS[pattern_name], input_str))

    @classmethod
    def sanitize_command(cls, command: str) -> str:
        """Sanitize command input"""
        # Remove any dangerous characters
        sanitized = re.sub(r'[;&|]', '', command)
        # Limit length
        return sanitized[:100]

    @classmethod
    def validate_config_value(cls, value: Any) -> bool:
        """Validate configuration value"""
        if isinstance(value, (str, int, float, bool)):
            return True
        if isinstance(value, (list, tuple)):
            return all(isinstance(x, (str, int, float, bool)) for x in value)
        if isinstance(value, dict):
            return all(
                isinstance(k, str) and isinstance(v, (str, int, float, bool))
                for k, v in value.items()
            )
        return False

    @classmethod
    def validate_memory_entry(cls, entry: Dict[str, Any]) -> bool:
        """Validate memory entry structure"""
        required_fields = {'type', 'data'}
        if not all(field in entry for field in required_fields):
            return False
        
        if not cls.validate_pattern(entry['type'], 'memory_type'):
            return False
            
        if not isinstance(entry['data'], dict):
            return False
            
        return True

    @classmethod
    def sanitize_log_message(cls, message: str) -> str:
        """Sanitize log messages to prevent log injection"""
        # Remove newlines and control characters
        sanitized = re.sub(r'[\n\r\t]', ' ', message)
        # Escape JSON special characters
        sanitized = re.sub(r'["\\\x00-\x1f]', '', sanitized)
        return sanitized[:1000]  # Limit length
