import os

CONFIG = {
    'LLAMAFILE_PATH': '/usr/local/bin/llamafile',
    'MODEL_PATH': 'tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf',
    'LOG_DIR': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs'),
    'MEMORY_DIR': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'memory'),
    
    # System monitoring settings
    'MONITORING_INTERVAL': 60,  # seconds
    'CPU_THRESHOLD': 80,  # percentage
    'MEMORY_THRESHOLD': 80,  # percentage
    'DISK_THRESHOLD': 90,  # percentage
    
    # Security settings
    'ALLOWED_COMMANDS': [
        'ps', 'top', 'df', 'du', 'free',
        'netstat', 'ss', 'ip', 'ifconfig',
        'systemctl status', 'journalctl'
    ],
    'BLOCKED_COMMANDS': [
        'rm -rf', 'mkfs', 'dd',
        'shutdown', 'reboot',
        'chmod 777', 'chown -R'
    ],
    
    # Memory settings
    'SHORT_TERM_MEMORY_SIZE': 1000,
    'LONG_TERM_MEMORY_FILE': 'long_term_memory.json'
}
