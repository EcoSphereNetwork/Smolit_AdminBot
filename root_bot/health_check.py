import os
import psutil
import logging
from typing import Dict, Any
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Prometheus metrics
REQUEST_COUNT = Counter('rootbot_requests_total', 'Total number of requests')
MEMORY_USAGE = Gauge('rootbot_memory_usage_bytes', 'Memory usage in bytes')
CPU_USAGE = Gauge('rootbot_cpu_usage_percent', 'CPU usage percentage')
RESPONSE_TIME = Histogram('rootbot_response_time_seconds', 'Response time in seconds')

class HealthCheck:
    """Health check and metrics collection for RootBot"""
    
    def __init__(self, bot):
        self.logger = logging.getLogger('RootBot.health')
        self.bot = bot
        
        # Start Prometheus metrics server
        start_http_server(5000)
        
    def check_health(self) -> Dict[str, Any]:
        """Perform health check and collect metrics"""
        try:
            # Update metrics
            process = psutil.Process(os.getpid())
            MEMORY_USAGE.set(process.memory_info().rss)
            CPU_USAGE.set(process.cpu_percent())
            REQUEST_COUNT.inc()
            
            # Check component health
            health_status = {
                'status': 'healthy',
                'components': {
                    'security_manager': self._check_security_manager(),
                    'process_monitor': self._check_process_monitor(),
                    'resource_monitor': self._check_resource_monitor(),
                    'task_manager': self._check_task_manager()
                },
                'metrics': {
                    'memory_usage': process.memory_info().rss,
                    'cpu_usage': process.cpu_percent(),
                    'thread_count': process.num_threads()
                }
            }
            
            # Check if any component is unhealthy
            if any(not status['healthy'] for status in health_status['components'].values()):
                health_status['status'] = 'degraded'
                
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
            
    def _check_security_manager(self) -> Dict[str, Any]:
        """Check security manager health"""
        try:
            integrity_check = self.bot.security_manager.verify_file_integrity('config')
            return {
                'healthy': integrity_check,
                'message': 'Security checks passing' if integrity_check else 'Security check failed'
            }
        except Exception as e:
            return {
                'healthy': False,
                'message': f'Security manager error: {str(e)}'
            }
            
    def _check_process_monitor(self) -> Dict[str, Any]:
        """Check process monitor health"""
        try:
            pid = self.bot.process_monitor.read_pid()
            is_running = self.bot.process_monitor.is_process_running(pid) if pid else False
            return {
                'healthy': is_running,
                'message': f'Process running with PID {pid}' if is_running else 'Process not running'
            }
        except Exception as e:
            return {
                'healthy': False,
                'message': f'Process monitor error: {str(e)}'
            }
            
    def _check_resource_monitor(self) -> Dict[str, Any]:
        """Check resource monitor health"""
        try:
            metrics = self.bot.resource_monitor.check_resources()
            has_alerts = 'alerts' in metrics
            return {
                'healthy': not has_alerts,
                'message': 'Resources within limits' if not has_alerts else 'Resource alerts present'
            }
        except Exception as e:
            return {
                'healthy': False,
                'message': f'Resource monitor error: {str(e)}'
            }
            
    def _check_task_manager(self) -> Dict[str, Any]:
        """Check task manager health"""
        try:
            active_tasks = len(self.bot.task_manager.active_tasks)
            return {
                'healthy': True,
                'message': f'Task manager active with {active_tasks} tasks'
            }
        except Exception as e:
            return {
                'healthy': False,
                'message': f'Task manager error: {str(e)}'
            }
