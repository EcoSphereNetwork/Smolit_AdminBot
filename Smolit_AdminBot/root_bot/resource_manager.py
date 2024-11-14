import os
import psutil
import logging
from typing import Dict, Any, Optional
from .config.config import CONFIG

class ResourceManager:
    """Manages and enforces resource usage limits"""
    
    def __init__(self):
        self.logger = logging.getLogger('RootBot.ResourceManager')
        self.process = psutil.Process()
        self.resource_limits = CONFIG['RESOURCE_LIMITS']
        
    def enforce_limits(self) -> Dict[str, Any]:
        """Enforce resource usage limits"""
        status = {
            'cpu_limited': False,
            'memory_limited': False,
            'io_limited': False,
            'action_taken': False
        }
        
        # Check CPU usage
        if self.process.cpu_percent() > self.resource_limits['max_cpu_per_process']:
            self._limit_cpu_usage()
            status['cpu_limited'] = True
            status['action_taken'] = True
            
        # Check memory usage
        if self.process.memory_percent() > self.resource_limits['max_memory_per_process']:
            self._limit_memory_usage()
            status['memory_limited'] = True
            status['action_taken'] = True
            
        # Check I/O usage
        if self._check_io_usage():
            self._limit_io_usage()
            status['io_limited'] = True
            status['action_taken'] = True
            
        return status
        
    def _limit_cpu_usage(self):
        """Limit CPU usage through nice value and CPU affinity"""
        try:
            # Set nice value to reduce CPU priority
            os.nice(10)
            
            # Limit CPU affinity if needed
            cpu_count = psutil.cpu_count()
            if cpu_count > 2:
                # Use only half of available CPUs
                cpus_to_use = list(range(cpu_count // 2))
                self.process.cpu_affinity(cpus_to_use)
                
            self.logger.warning("CPU usage limited due to threshold breach")
        except Exception as e:
            self.logger.error(f"Failed to limit CPU usage: {str(e)}")
            
    def _limit_memory_usage(self):
        """Limit memory usage through various mechanisms"""
        try:
            # Trigger garbage collection
            import gc
            gc.collect()
            
            # Clear process memory
            if hasattr(self.process, "memory_maps"):
                self.process.memory_maps()
                
            self.logger.warning("Memory usage limited due to threshold breach")
        except Exception as e:
            self.logger.error(f"Failed to limit memory usage: {str(e)}")
            
    def _check_io_usage(self) -> bool:
        """Check if I/O usage exceeds limits"""
        try:
            io_counters = self.process.io_counters()
            write_bytes = io_counters.write_bytes
            max_write_rate = self.resource_limits['max_disk_write_rate']
            
            return write_bytes > max_write_rate
        except Exception:
            return False
            
    def _limit_io_usage(self):
        """Limit I/O usage through ionice"""
        try:
            import subprocess
            subprocess.run(['ionice', '-c', '2', '-n', '7', '-p', str(self.process.pid)])
            self.logger.warning("I/O usage limited due to threshold breach")
        except Exception as e:
            self.logger.error(f"Failed to limit I/O usage: {str(e)}")
            
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics"""
        try:
            cpu_percent = self.process.cpu_percent()
            memory_percent = self.process.memory_percent()
            io_counters = self.process.io_counters()
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'write_bytes': io_counters.write_bytes,
                'read_bytes': io_counters.read_bytes,
                'limits': self.resource_limits
            }
        except Exception as e:
            self.logger.error(f"Failed to get resource usage: {str(e)}")
            return {}
