import os
import time
import psutil
import logging
from typing import Optional
from datetime import datetime

class ProcessMonitor:
    """Monitors and manages the RootBot process"""
    
    def __init__(self, pid_file: str = "/var/run/rootbot.pid"):
        self.logger = logging.getLogger('RootBot.monitor')
        self.pid_file = pid_file
        self.last_health_check = 0
        self.health_check_interval = 60  # seconds
        
    def write_pid(self) -> None:
        """Write current process PID to file"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            os.chmod(self.pid_file, 0o600)
        except Exception as e:
            self.logger.error(f"Failed to write PID file: {str(e)}")
            raise
            
    def read_pid(self) -> Optional[int]:
        """Read PID from file"""
        try:
            if os.path.exists(self.pid_file):
                with open(self.pid_file, 'r') as f:
                    return int(f.read().strip())
        except Exception as e:
            self.logger.error(f"Failed to read PID file: {str(e)}")
        return None
        
    def is_process_running(self, pid: Optional[int] = None) -> bool:
        """Check if process is running"""
        if pid is None:
            pid = self.read_pid()
            
        if pid is None:
            return False
            
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:
            return False
            
    def check_health(self) -> bool:
        """Perform health check on the process"""
        current_time = time.time()
        if current_time - self.last_health_check < self.health_check_interval:
            return True
            
        pid = self.read_pid()
        if not pid:
            self.logger.error("No PID file found")
            return False
            
        try:
            process = psutil.Process(pid)
            
            # Check CPU and memory usage
            cpu_percent = process.cpu_percent(interval=1)
            mem_info = process.memory_info()
            
            # Log health metrics
            self.logger.info(
                "Health check",
                extra={
                    'cpu_percent': cpu_percent,
                    'memory_rss': mem_info.rss,
                    'memory_vms': mem_info.vms,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Update last check time
            self.last_health_check = current_time
            
            # Consider unhealthy if CPU usage is too high
            return cpu_percent < 90
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False

    def cleanup(self) -> None:
        """Clean up PID file"""
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
        except Exception as e:
            self.logger.error(f"Failed to cleanup PID file: {str(e)}")
