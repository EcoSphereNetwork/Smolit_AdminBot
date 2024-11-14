import os

CONFIG = {
    # Version Control
    'VERSION_CHECK': True,
    'AUTO_UPDATE': False,
    
    # LlamaFile settings
    'LLAMAFILE_PATH': '/usr/local/bin/llamafile',
    'MODEL_PATH': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models/Llama-3.2-1B-Instruct.Q6_K.llamafile'),
    'LLAMAFILE_PORT': 8080,
    'LLAMAFILE_SETTINGS': {
        'ctx_size': 4096,
        'threads': os.cpu_count() or 4,
        'temp': 0.7,
        'repeat_penalty': 1.1,
        'embedding': True,
        'gpu_layers': 0  # Set to higher number if GPU available
    },
    
    # Directory settings
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
    },
    
    # Notification settings
    'NOTIFICATIONS': {
        'email': {
            'enabled': False,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'from': 'rootbot@example.com',
            'to': 'admin@example.com',
            'username': '',
            'password': ''
        },
        'slack': {
            'enabled': False,
            'webhook_url': ''
        },
        'telegram': {
            'enabled': False,
            'bot_token': '',
            'chat_id': ''
        }
    },
    
    # Logging settings
    'LOGGING': {
        'level': 'INFO',
        'format': '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
        'date_format': '%Y-%m-%d %H:%M:%S',
        'file_logging': True,
        'console_logging': True,
        'log_rotation': True,
        'max_log_size': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5
    },
    
    # Docker settings
    'DOCKER': {
        'resource_limits': {
            'default_memory': '2g',
            'default_cpu_shares': 1024,
            'max_memory_per_container': '4g',
            'max_cpu_shares': 2048
        },
        'monitoring': {
            'stats_interval': 30,  # seconds
            'alert_cpu_threshold': 80,  # percentage
            'alert_memory_threshold': 80,  # percentage
            'alert_disk_threshold': 80  # percentage
        },
        'security': {
            'privileged_mode': False,
            'allowed_capabilities': [],
            'default_seccomp_profile': True
        },
        'networking': {
            'default_network': 'bridge',
            'exposed_port_range': (8000, 9000)
        },
        'cleanup': {
            'auto_remove_stopped': False,
            'prune_interval': 86400,  # 24 hours
            'max_container_age': 604800  # 7 days
        }
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

