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
from transformers import AutoModelForCausalLM, AutoTokenizer
from .task_manager import TaskManager
from .event_handler import SystemEventHandler
from .recovery_manager import RecoveryManager
from .security_manager import SecurityManager

class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass

class LLMInterface:
    def __init__(self, model_name="Mozilla/Llama-3.2-1B-Instruct"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)

    def generate_response(self, prompt, max_length=50):
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(inputs.input_ids, max_length=max_length)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

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
        print("Initializing RootBot...")
        self.setup_logging()
        
        # Initialize security manager
        self.security_manager = SecurityManager({
            'config': os.path.join(CONFIG['CONFIG_DIR'], 'config.py'),
            'memory': os.path.join(CONFIG['MEMORY_DIR'], CONFIG['LONG_TERM_MEMORY_FILE']),
            'service': '/etc/systemd/system/rootbot.service'
        })
        
        # Verify critical files before proceeding
        if not all(self.security_manager.verify_file_integrity(f) for f in ['config', 'memory']):
            self.logger.critical("Critical file integrity check failed")
            raise SecurityError("File integrity verification failed")

        self.short_term_memory = deque(maxlen=CONFIG['SHORT_TERM_MEMORY_SIZE'])
        self.long_term_memory_path = os.path.join(
            CONFIG['MEMORY_DIR'],
            CONFIG['LONG_TERM_MEMORY_FILE']
        )
        self.load_long_term_memory()
        self.running = True
        self.last_maintenance = 0
        self.maintenance_interval = 3600  # 1 hour
        
        # Initialize components
        self.llm = LLMInterface()
        self.task_manager = TaskManager(self)
        self.event_handler = SystemEventHandler()
        self.recovery_manager = RecoveryManager()

        
        # Ensure LLM server is running
        if not self.llm._ensure_server_running():
            self.logger.error("Failed to start LLM server")

        
    def setup_logging(self):
        """Configure logging with structured JSON format and security audit trails"""
        log_file = os.path.join(CONFIG['LOG_DIR'], 
                               f'root_bot_{datetime.now().strftime("%Y%m%d")}.log')
        audit_file = os.path.join(CONFIG['LOG_DIR'],
                                f'audit_{datetime.now().strftime("%Y%m%d")}.log')
        
        # Main application logger
        main_handler = logging.FileHandler(log_file)
        main_handler.setFormatter(logging.Formatter(
            '{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s",'
            '"message":"%(message)s","module":"%(module)s"}'
        ))

    def save_long_term_memory(self):
        """Save long-term memory with integrity verification"""
        try:
            # Verify file integrity before saving
            if not self.security_manager.verify_file_integrity('memory'):
                self.logger.critical("Memory file integrity check failed before save")
                raise SecurityError("Memory file integrity compromised")

            memory_data = [entry.to_dict() for entry in self.long_term_memory]
            with open(self.long_term_memory_path, 'w') as f:
                json.dump(memory_data, f, indent=2)
            
            # Update hash after legitimate change
            self.security_manager.update_file_hash('memory')
            self.audit_logger.info(
                "Long-term memory updated",
                extra={'user': 'system', 'action': 'memory_update'}
            )
        except Exception as e:
            self.logger.error(f"Failed to save long-term memory: {str(e)}")
            raise

        
        # Security audit logger
        audit_handler = logging.FileHandler(audit_file)
        audit_handler.setFormatter(logging.Formatter(
            '{"timestamp":"%(asctime)s","level":"%(levelname)s","type":"security_audit",'
            '"event":"%(message)s","user":"%(user)s"}'
        ))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
        ))
        
        # Setup main logger
        self.logger = logging.getLogger('RootBot')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(main_handler)
        self.logger.addHandler(console_handler)
        
        # Setup audit logger
        self.audit_logger = logging.getLogger('RootBot.audit')
        self.audit_logger.setLevel(logging.INFO)
        self.audit_logger.addHandler(audit_handler)

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
        """Save long-term memory with integrity verification and atomic write"""
        try:
            # Verify file integrity before saving
            if not self.security_manager.verify_file_integrity('memory'):
                self.logger.critical("Memory file integrity check failed before save")
                raise SecurityError("Memory file integrity compromised")

            # Write to temporary file first
            temp_path = f"{self.long_term_memory_path}.tmp"
            with open(temp_path, 'w') as f:
                json.dump([entry.to_dict() for entry in self.long_term_memory], f)
            
            # Atomic rename
            os.replace(temp_path, self.long_term_memory_path)
            
            # Update hash after legitimate change
            self.security_manager.update_file_hash('memory')
            self.audit_logger.info(
                "Long-term memory updated",
                extra={'user': 'system', 'action': 'memory_update'}
            )
        except Exception as e:
            self.logger.error(f"Failed to save long-term memory: {str(e)}")
            raise

    def add_to_memory(self, 
                     event: Dict[str, Any], 
                     long_term: bool = False,
                     priority: int = 1) -> str:
        """Add event to memory with priority and deduplication"""
        entry = MemoryEntry(event['type'], event['data'], priority)
        
        if long_term:
            # Add only to long-term memory
            if not any(e.id == entry.id for e in self.long_term_memory):
                self.long_term_memory.append(entry)
                self.save_long_term_memory()
        else:
            # Add only to short-term memory
            if not any(e.id == entry.id for e in self.short_term_memory):
                self.short_term_memory.append(entry)
        
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
        
        # Set up filesystem monitoring for critical paths
        self.event_handler.monitor_filesystem(CONFIG['LOG_DIR'], 
            lambda path: self.add_to_memory({'type': 'file_change', 'path': path}, priority=3))
        
        # Register recovery callbacks
        self.event_handler.register_recovery_callback('cpu_percent',
            lambda value: self.recovery_manager.release_resources('high_cpu_process', value))
        self.event_handler.register_recovery_callback('memory_percent',
            lambda value: self.recovery_manager.release_resources('high_memory_process', value))
        
        while self.running:
            try:
                # Monitor system metrics
                metrics = self.monitor_system()
                if metrics:
                    # Check system health
                    health_metrics = self.event_handler.check_system_health()
                    for metric, value in health_metrics.items():
                        if value > self.event_handler.metrics_thresholds.get(metric, 90):
                            self.event_handler.handle_threshold_breach(metric, value)
                            self.add_to_memory({
                                'type': 'threshold_breach',
                                'metric': metric,
                                'value': value
                            }, long_term=True, priority=4)
                    
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
                        try:
                            analysis = self.llm.analyze_system_state(metrics)
                            if analysis['status'] != 'normal':
                                self.add_to_memory({
                                    'type': 'system_analysis',
                                    'analysis': analysis
                                }, long_term=True, priority=4)
                        except Exception as e:
                            self.logger.error(f"LLM analysis failed: {e}")
                            self.recovery_manager.handle_llm_failure()
                
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
        
        # Stop event monitoring
        self.event_handler.stop_monitoring()
        
        # Shutdown LLM interface
        if hasattr(self, 'llm'):
            self.llm.shutdown()
        
        # Save memory state
        self.save_long_term_memory()
        
        # Final cleanup
        self.recovery_manager.cleanup_temp_files(CONFIG['LOG_DIR'])
        
        self.logger.info("RootBot shutdown complete")

            except Exception as e:
                self.logger.error(f"Error in main loop: {str(e)}")
                time.sleep(CONFIG['MONITORING_INTERVAL'])

                self.logger.error(f"Error in main loop: {str(e)}")
                time.sleep(CONFIG['MONITORING_INTERVAL'])







