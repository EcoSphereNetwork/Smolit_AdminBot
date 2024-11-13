import os
import json
import time
import logging
import subprocess
import psutil
from datetime import datetime
from collections import deque
from typing import List, Dict, Any
from .config.config import CONFIG

class RootBot:
    def __init__(self):
        self.setup_logging()
        self.short_term_memory = deque(maxlen=CONFIG['SHORT_TERM_MEMORY_SIZE'])
        self.long_term_memory_path = os.path.join(
            CONFIG['MEMORY_DIR'],
            CONFIG['LONG_TERM_MEMORY_FILE']
        )
        self.load_long_term_memory()
        self.running = True
        
    def setup_logging(self):
        """Configure logging with proper format and security measures"""
        log_file = os.path.join(CONFIG['LOG_DIR'], f'root_bot_{datetime.now().strftime("%Y%m%d")}.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('RootBot')
        
    def load_long_term_memory(self):
        """Load long-term memory from disk with error handling"""
        try:
            if os.path.exists(self.long_term_memory_path):
                with open(self.long_term_memory_path, 'r') as f:
                    self.long_term_memory = json.load(f)
            else:
                self.long_term_memory = []
                self.save_long_term_memory()
        except Exception as e:
            self.logger.error(f"Failed to load long-term memory: {str(e)}")
            self.long_term_memory = []

    def save_long_term_memory(self):
        """Save long-term memory to disk with error handling"""
        try:
            with open(self.long_term_memory_path, 'w') as f:
                json.dump(self.long_term_memory, f)
        except Exception as e:
            self.logger.error(f"Failed to save long-term memory: {str(e)}")

    def add_to_memory(self, event: Dict[str, Any], long_term: bool = False):
        """Add event to memory with timestamp and proper categorization"""
        event['timestamp'] = datetime.now().isoformat()
        self.short_term_memory.append(event)
        
        if long_term:
            self.long_term_memory.append(event)
            self.save_long_term_memory()

    def is_command_safe(self, command: str) -> bool:
        """Validate if a command is safe to execute"""
        command = command.lower().strip()
        
        # Check against blocked commands
        for blocked in CONFIG['BLOCKED_COMMANDS']:
            if blocked in command:
                self.logger.warning(f"Blocked command attempted: {command}")
                return False
                
        # Check if command is in allowed list
        for allowed in CONFIG['ALLOWED_COMMANDS']:
            if command.startswith(allowed):
                return True
                
        return False

    def execute_command(self, command: str) -> tuple:
        """Safely execute system commands with proper error handling"""
        if not self.is_command_safe(command):
            return False, "Command not allowed for security reasons"
            
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=30)
            
            self.add_to_memory({
                'type': 'command_execution',
                'command': command,
                'success': process.returncode == 0
            })
            
            return process.returncode == 0, stdout if process.returncode == 0 else stderr
            
        except subprocess.TimeoutExpired:
            process.kill()
            return False, "Command timed out"
        except Exception as e:
            self.logger.error(f"Command execution error: {str(e)}")
            return False, str(e)

    def monitor_system(self):
        """Collect system metrics and status"""
        try:
            metrics = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'network_connections': len(psutil.net_connections()),
                'timestamp': datetime.now().isoformat()
            }
            
            self.add_to_memory({
                'type': 'system_metrics',
                'metrics': metrics
            })
            
            # Check thresholds and log warnings
            if metrics['cpu_percent'] > CONFIG['CPU_THRESHOLD']:
                self.logger.warning(f"High CPU usage: {metrics['cpu_percent']}%")
            if metrics['memory_percent'] > CONFIG['MEMORY_THRESHOLD']:
                self.logger.warning(f"High memory usage: {metrics['memory_percent']}%")
            if metrics['disk_usage'] > CONFIG['DISK_THRESHOLD']:
                self.logger.warning(f"High disk usage: {metrics['disk_usage']}%")
                
            return metrics
            
        except Exception as e:
            self.logger.error(f"System monitoring error: {str(e)}")
            return None

    def run(self):
        """Main bot loop"""
        self.logger.info("RootBot started")
        
        while self.running:
            try:
                # Monitor system
                metrics = self.monitor_system()
                if metrics:
                    # TODO: Add decision making based on metrics
                    pass
                    
                # Sleep for the monitoring interval
                time.sleep(CONFIG['MONITORING_INTERVAL'])
                
            except KeyboardInterrupt:
                self.logger.info("Shutting down RootBot...")
                self.running = False
            except Exception as e:
                self.logger.error(f"Error in main loop: {str(e)}")
                time.sleep(CONFIG['MONITORING_INTERVAL'])

    def shutdown(self):
        """Graceful shutdown procedure"""
        self.running = False
        self.save_long_term_memory()
        self.logger.info("RootBot shutdown complete")
