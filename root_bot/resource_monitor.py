import os
import psutil
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from .error_handler import RootBotError

class ResourceMonitorError(RootBotError):
    """Raised for resource monitoring errors"""
    pass

class ResourceMonitor:
    """Monitors system resources and triggers alerts"""
    
    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        self.logger = logging.getLogger('RootBot.resources')
        self.thresholds = thresholds or {
            'cpu_percent': 90.0,      # CPU usage threshold (%)
            'memory_percent': 85.0,    # Memory usage threshold (%)
            'disk_percent': 90.0,      # Disk usage threshold (%)
            'swap_percent': 80.0       # Swap usage threshold (%)
        }
        
    def check_resources(self) -> Dict[str, Any]:
        """Check system resources and return metrics"""
        try:
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu': self._get_cpu_metrics(),
                'memory': self._get_memory_metrics(),
                'disk': self._get_disk_metrics(),
                'network': self._get_network_metrics()
            }
            
            # Check for threshold violations
            alerts = self._check_thresholds(metrics)
            if alerts:
                metrics['alerts'] = alerts
                
            return metrics
            
        except Exception as e:
            raise ResourceMonitorError("Failed to check resources", {'error': str(e)})
            
    def _get_cpu_metrics(self) -> Dict[str, float]:
        """Get CPU-related metrics"""
        return {
            'percent': psutil.cpu_percent(interval=1),
            'load_avg': os.getloadavg(),
            'count': psutil.cpu_count()
        }
        
    def _get_memory_metrics(self) -> Dict[str, Any]:
        """Get memory-related metrics"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            'total': mem.total,
            'available': mem.available,
            'percent': mem.percent,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_percent': swap.percent
        }
        
    def _get_disk_metrics(self) -> Dict[str, Any]:
        """Get disk-related metrics"""
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }
        
    def _get_network_metrics(self) -> Dict[str, Any]:
        """Get network-related metrics"""
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'error_in': net_io.errin,
            'error_out': net_io.errout
        }
        
    def _check_thresholds(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Check metrics against thresholds and return alerts"""
        alerts = {}
        
        # CPU check
        if metrics['cpu']['percent'] > self.thresholds['cpu_percent']:
            alerts['cpu'] = {
                'current': metrics['cpu']['percent'],
                'threshold': self.thresholds['cpu_percent']
            }
            
        # Memory check
        if metrics['memory']['percent'] > self.thresholds['memory_percent']:
            alerts['memory'] = {
                'current': metrics['memory']['percent'],
                'threshold': self.thresholds['memory_percent']
            }
            
        # Disk check
        if metrics['disk']['percent'] > self.thresholds['disk_percent']:
            alerts['disk'] = {
                'current': metrics['disk']['percent'],
                'threshold': self.thresholds['disk_percent']
            }
            
        # Swap check
        if metrics['memory']['swap_percent'] > self.thresholds['swap_percent']:
            alerts['swap'] = {
                'current': metrics['memory']['swap_percent'],
                'threshold': self.thresholds['swap_percent']
            }
            
        return alerts if alerts else None
