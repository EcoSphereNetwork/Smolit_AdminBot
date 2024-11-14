import os
from typing import Dict, Any, List, Tuple
from .config.config import CONFIG

class ConfigValidator:
    """Validates configuration parameters and ensures proper setup"""
    
    REQUIRED_PARAMS = {
        'LLAMAFILE_PATH': str,
        'MODEL_PATH': str,
        'LOG_DIR': str,
        'MEMORY_DIR': str,
        'MONITORING_INTERVAL': int,
        'CPU_THRESHOLD': int,
        'MEMORY_THRESHOLD': int,
        'DISK_THRESHOLD': int,
        'SHORT_TERM_MEMORY_SIZE': int,
        'LONG_TERM_MEMORY_FILE': str
    }
    
    REQUIRED_DIRS = [
        'LOG_DIR',
        'MEMORY_DIR'
    ]
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_config(self) -> Tuple[bool, List[str], List[str]]:
        """Validate all configuration parameters"""
        self._check_required_params()
        self._check_thresholds()
        self._check_directories()
        self._check_permissions()
        self._validate_commands()
        self._validate_resource_limits()
        
        return len(self.errors) == 0, self.errors, self.warnings
        
    def _check_required_params(self):
        """Check if all required parameters exist and have correct types"""
        for param, expected_type in self.REQUIRED_PARAMS.items():
            if param not in CONFIG:
                self.errors.append(f"Missing required parameter: {param}")
            elif not isinstance(CONFIG[param], expected_type):
                self.errors.append(
                    f"Invalid type for {param}: expected {expected_type.__name__}, "
                    f"got {type(CONFIG[param]).__name__}"
                )
                
    def _check_thresholds(self):
        """Validate threshold values"""
        thresholds = ['CPU_THRESHOLD', 'MEMORY_THRESHOLD', 'DISK_THRESHOLD']
        for threshold in thresholds:
            if threshold in CONFIG:
                value = CONFIG[threshold]
                if not (0 <= value <= 100):
                    self.errors.append(f"{threshold} must be between 0 and 100")
                elif value > 90:
                    self.warnings.append(f"{threshold} is set very high ({value}%)")
                    
    def _check_directories(self):
        """Check if required directories exist and are writable"""
        for dir_param in self.REQUIRED_DIRS:
            if dir_param in CONFIG:
                dir_path = CONFIG[dir_param]
                if not os.path.exists(dir_path):
                    try:
                        os.makedirs(dir_path, mode=0o750)
                    except Exception as e:
                        self.errors.append(f"Failed to create {dir_param} directory: {str(e)}")
                elif not os.access(dir_path, os.W_OK):
                    self.errors.append(f"No write permission for {dir_param}: {dir_path}")
                    
    def _check_permissions(self):
        """Check file and directory permissions"""
        for dir_param in self.REQUIRED_DIRS:
            if dir_param in CONFIG:
                dir_path = CONFIG[dir_param]
                if os.path.exists(dir_path):
                    mode = os.stat(dir_path).st_mode & 0o777
                    if mode & 0o077:  # Check if group/others have too many permissions
                        self.warnings.append(
                            f"{dir_param} permissions are too permissive: {oct(mode)}"
                        )
                        
    def _validate_commands(self):
        """Validate command lists"""
        if 'ALLOWED_COMMANDS' not in CONFIG:
            self.errors.append("Missing ALLOWED_COMMANDS configuration")
        elif not isinstance(CONFIG['ALLOWED_COMMANDS'], list):
            self.errors.append("ALLOWED_COMMANDS must be a list")
            
        if 'BLOCKED_COMMANDS' not in CONFIG:
            self.errors.append("Missing BLOCKED_COMMANDS configuration")
        elif not isinstance(CONFIG['BLOCKED_COMMANDS'], list):
            self.errors.append("BLOCKED_COMMANDS must be a list")
            
        # Check for conflicts
        if ('ALLOWED_COMMANDS' in CONFIG and 'BLOCKED_COMMANDS' in CONFIG and
            isinstance(CONFIG['ALLOWED_COMMANDS'], list) and 
            isinstance(CONFIG['BLOCKED_COMMANDS'], list)):
            allowed = set(CONFIG['ALLOWED_COMMANDS'])
            blocked = set(CONFIG['BLOCKED_COMMANDS'])
            conflicts = allowed.intersection(blocked)
            if conflicts:
                self.errors.append(
                    f"Commands appear in both allowed and blocked lists: {conflicts}"
                )
                
    def _validate_resource_limits(self):
        """Validate resource limit configurations"""
        if 'RESOURCE_LIMITS' not in CONFIG:
            self.errors.append("Missing RESOURCE_LIMITS configuration")
            return
            
        limits = CONFIG['RESOURCE_LIMITS']
        if not isinstance(limits, dict):
            self.errors.append("RESOURCE_LIMITS must be a dictionary")
            return
            
        required_limits = {
            'max_cpu_per_process': (0, 100),
            'max_memory_per_process': (0, 100),
            'max_disk_write_rate': (0, None)
        }
        
        for limit, (min_val, max_val) in required_limits.items():
            if limit not in limits:
                self.errors.append(f"Missing resource limit: {limit}")
            elif not isinstance(limits[limit], (int, float)):
                self.errors.append(f"Invalid type for {limit}")
            elif min_val is not None and limits[limit] < min_val:
                self.errors.append(f"{limit} is below minimum value {min_val}")
            elif max_val is not None and limits[limit] > max_val:
                self.errors.append(f"{limit} exceeds maximum value {max_val}")
