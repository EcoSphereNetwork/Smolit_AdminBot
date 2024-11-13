import os
import json
import time
import logging
import subprocess
import psutil
from datetime import datetime
from collections import deque
from typing import List, Dict, Any, Optional, Union
from .config.config import CONFIG

class MemoryEntry:
    """Structured memory entry with metadata"""
    def __init__(self, entry_type: str, data: Dict[str, Any], priority: int = 1):
        self.timestamp = datetime.now().isoformat()
        self.type = entry_type
        self.data = data
        self.priority = priority  # 1 (low) to 5 (high)
        self.id = f"{int(time.time())}_{hash(str(data))}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'type': self.type,
            'data': self.data,
            'priority': self.priority
        }

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
        self.last_maintenance = 0
        self.maintenance_interval = 3600  # 1 hour
        
    def setup_logging(self):
        """Configure logging with proper format and security measures"""
        log_file = os.path.join(CONFIG['LOG_DIR'], 
                               f'root_bot_{datetime.now().strftime("%Y%m%d")}.log')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('RootBot')
        
    def load_long_term_memory(self):
        """Load long-term memory with error recovery"""
        try:
            if os.path.exists(self.long_term_memory_path):
                with open(self.long_term_memory_path, 'r') as f:
                    data = json.load(f)
                    self.long_term_memory = [
                        MemoryEntry(entry['type'], entry['data'], entry.get('priority', 1))
                        for entry in data
                    ]
            else:
                self.long_term_memory = []
                self.save_long_term_memory()
        except Exception as e:
            self.logger.error(f"Failed to load long-term memory: {str(e)}")
            self.long_term_memory = []
            # Create backup of corrupted file if it exists
            if os.path.exists(self.long_term_memory_path):
                backup_path = f"{self.long_term_memory_path}.bak"
                try:
                    os.rename(self.long_term_memory_path, backup_path)
                    self.logger.info(f"Created backup of corrupted memory file: {backup_path}")
                except Exception as be:
                    self.logger.error(f"Failed to create memory backup: {str(be)}")

    def save_long_term_memory(self):
        """Save long-term memory with atomic write"""
        try:
            # Write to temporary file first
            temp_path = f"{self.long_term_memory_path}.tmp"
            with open(temp_path, 'w') as f:
                json.dump([entry.to_dict() for entry in self.long_term_memory], f)
            # Atomic rename
            os.replace(temp_path, self.long_term_memory_path)
        except Exception as e:
            self.logger.error(f"Failed to save long-term memory: {str(e)}")

    def add_to_memory(self, 
                     event: Dict[str, Any], 
                     long_term: bool = False,
                     priority: int = 1) -> str:
        """Add event to memory with priority and deduplication"""
        entry = MemoryEntry(event['type'], event, priority)
        
        # Check for duplicates in short-term memory
        if not any(e.id == entry.id for e in self.short_term_memory):
            self.short_term_memory.append(entry)
        
        if long_term:
            # Check for duplicates in long-term memory
            if not any(e.id == entry.id for e in self.long_term_memory):
                self.long_term_memory.append(entry)
                self.save_long_term_memory()
        
        return entry.id

    def query_memory(self, 
                    entry_type: Optional[str] = None,
                    time_range: Optional[tuple] = None,
                    priority_min: int = 1) -> List[Dict[str, Any]]:
        """Query memory with filtering and sorting"""
        results = []
        
        # Combine both memories for searching
        all_memories = list(self.short_term_memory) + self.long_term_memory
        
        for entry in all_memories:
            if entry.priority < priority_min:
                continue
                
            if entry_type and entry.type != entry_type:
                continue
                
            if time_range:
                entry_time = datetime.fromisoformat(entry.timestamp)
                if not (time_range[0] <= entry_time <= time_range[1]):
                    continue
                    
            results.append(entry.to_dict())
        
        # Sort by timestamp and priority
        results.sort(key=lambda x: (x['timestamp'], x['priority']), reverse=True)
        return results

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

    def monitor_system(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics"""
        try:
            metrics = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'network_connections': len(psutil.net_connections()),
                'load_average': os.getloadavg(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Add CPU frequency if available
            try:
                cpu_freq = psutil.cpu_freq()
                if cpu_freq:
                    metrics['cpu_freq'] = {
                        'current': cpu_freq.current,
                        'min': cpu_freq.min,
                        'max': cpu_freq.max
                    }
            except Exception:
                pass
            
            # Add memory details
            mem = psutil.virtual_memory()
            metrics['memory_details'] = {
                'total': mem.total,
                'available': mem.available,
                'used': mem.used,
                'free': mem.free,
                'cached': mem.cached if hasattr(mem, 'cached') else None
            }
            
            # Add system uptime
            metrics['uptime'] = time.time() - psutil.boot_time()
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"System monitoring error: {str(e)}")
            return None

    def perform_maintenance(self):
        """Perform periodic maintenance tasks"""
        current_time = time.time()
        if current_time - self.last_maintenance < self.maintenance_interval:
            return
            
        try:
            # Clean old logs
            self._clean_old_logs()
            
            # Compact memory if needed
            self._compact_memory()
            
            # Update maintenance timestamp
            self.last_maintenance = current_time
            
        except Exception as e:
            self.logger.error(f"Maintenance error: {str(e)}")

    def _clean_old_logs(self, max_age_days: int = 7):
        """Clean logs older than specified days"""
        try:
            current_time = time.time()
            log_dir = CONFIG['LOG_DIR']
            for log_file in os.listdir(log_dir):
                file_path = os.path.join(log_dir, log_file)
                if os.path.getmtime(file_path) < current_time - (max_age_days * 86400):
                    os.remove(file_path)
                    self.logger.info(f"Removed old log file: {log_file}")
        except Exception as e:
            self.logger.error(f"Error cleaning old logs: {str(e)}")

    def _compact_memory(self, threshold: int = 1000):
        """Compact long-term memory if it exceeds threshold"""
        if len(self.long_term_memory) > threshold:
            # Keep high priority and recent entries
            sorted_memory = sorted(
                self.long_term_memory,
                key=lambda x: (x.priority, x.timestamp),
                reverse=True
            )
            self.long_term_memory = sorted_memory[:threshold]
            self.save_long_term_memory()
            self.logger.info("Performed memory compaction")

    def run(self):
        """Main bot loop with enhanced error handling"""
        self.logger.info("RootBot started")
        
        while self.running:
            try:
                # Monitor system
                metrics = self.monitor_system()
                if metrics:
                    # Store metrics in memory
                    self.add_to_memory({
                        'type': 'system_metrics',
                        'metrics': metrics
                    })
                    
                    # Let task manager handle the metrics
                    if hasattr(self, 'task_manager'):
                        self.task_manager.manage_resources(metrics)
                    
                    # Get LLM analysis if available
                    if hasattr(self, 'llm'):
                        analysis = self.llm.analyze_system_state(metrics)
                        if analysis['status'] != 'normal':
                            self.add_to_memory({
                                'type': 'system_analysis',
                                'analysis': analysis
                            }, long_term=True, priority=4)
                
                # Perform maintenance if needed
                self.perform_maintenance()
                    
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

