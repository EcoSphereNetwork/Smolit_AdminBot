import os

CONFIG = {
    # LlamaFile settings
    'LLAMAFILE_PATH': '/usr/local/bin/llamafile',
    'MODEL_PATH': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf'),
    'LLAMAFILE_PORT': 8080,
    'LLAMAFILE_SETTINGS': {
        'ctx_size': 2048,
        'threads': os.cpu_count() or 4,
        'temp': 0.7,
        'embedding': True,
        'gpu_layers': 0  # Set to higher number if GPU available
    },
    
    'LOG_DIR': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs'),
    'MEMORY_DIR': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'memory'),
    
    # System monitoring settings
    'MONITORING_INTERVAL': 60,  # seconds
    'CPU_THRESHOLD': 80,  # percentage
    'MEMORY_THRESHOLD': 80,  # percentage
    'DISK_THRESHOLD': 90,  # percentage
    
    # Memory settings
    'SHORT_TERM_MEMORY_SIZE': 1000,
    'LONG_TERM_MEMORY_FILE': 'long_term_memory.json',
    'MEMORY_COMPACTION_THRESHOLD': 10000,
    'MEMORY_PRIORITY_LEVELS': {
        'system_critical': 5,
        'security_alert': 4,
        'resource_alert': 3,
        'system_warning': 2,
        'info': 1
    },
    
    # Security settings
    'ALLOWED_COMMANDS': [
        'ps', 'top', 'df', 'du', 'free',
        'netstat', 'ss', 'ip', 'ifconfig',
        'systemctl status', 'journalctl',
        'uptime', 'w', 'who', 'last',
        'lsof', 'iostat', 'vmstat', 'mpstat'
    ],
    'BLOCKED_COMMANDS': [
        'rm -rf', 'mkfs', 'dd',
        'shutdown', 'reboot',
        'chmod 777', 'chown -R',
        'passwd', 'useradd', 'usermod',
        'eval', 'exec', 'fork', 'system'
    ],
    
    # Resource management
    'RESOURCE_LIMITS': {
        'max_cpu_per_process': 50,  # percentage
        'max_memory_per_process': 25,  # percentage
        'max_disk_write_rate': 50 * 1024 * 1024,  # 50MB/s
        'max_open_files': 1000
    },
    
    # Maintenance settings
    'LOG_RETENTION_DAYS': 7,
    'BACKUP_RETENTION_DAYS': 30,
    'MAINTENANCE_INTERVAL': 3600,  # 1 hour
    
    # Analysis settings
    'ANOMALY_DETECTION': {
        'threshold_std_dev': 2.0,
        'min_data_points': 10,
        'window_size': 100
    }
}

# Ensure required directories exist
required_dirs = [
    CONFIG['LOG_DIR'],
    CONFIG['MEMORY_DIR'],
    os.path.dirname(CONFIG['MODEL_PATH'])
]

for dir_path in required_dirs:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
