import os
import time
import logging
from typing import List, Dict, Any
from datetime import datetime
import psutil
import subprocess
from .config.config import CONFIG

class TaskManager:
    def __init__(self, root_bot):
        self.root_bot = root_bot
        self.logger = logging.getLogger('RootBot.TaskManager')
        self.active_tasks = {}

    def get_process_info(self) -> List[Dict[str, Any]]:
        """Safely gather information about running processes"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    processes.append({
                        'pid': pinfo['pid'],
                        'name': pinfo['name'],
                        'cpu_percent': pinfo['cpu_percent'],
                        'memory_percent': pinfo['memory_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"Error gathering process info: {str(e)}")
        return processes

    def get_service_status(self) -> List[Dict[str, Any]]:
        """Get status of important system services"""
        services = []
        try:
            cmd = "systemctl list-units --type=service --state=running"
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n')[1:-7]:  # Skip header and footer
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            services.append({
                                'name': parts[0],
                                'status': parts[3]
                            })
        except Exception as e:
            self.logger.error(f"Error getting service status: {str(e)}")
        return services

    def monitor_network(self) -> Dict[str, Any]:
        """Monitor network interfaces and connections"""
        network_info = {
            'interfaces': [],
            'connections': 0,
            'bytes_sent': 0,
            'bytes_recv': 0
        }
        
        try:
            # Get network interface statistics
            net_io = psutil.net_io_counters(pernic=True)
            for interface, stats in net_io.items():
                network_info['interfaces'].append({
                    'name': interface,
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv
                })
                network_info['bytes_sent'] += stats.bytes_sent
                network_info['bytes_recv'] += stats.bytes_recv

            # Count active connections
            network_info['connections'] = len(psutil.net_connections())
            
        except Exception as e:
            self.logger.error(f"Error monitoring network: {str(e)}")
            
        return network_info

    def check_disk_health(self) -> Dict[str, Any]:
        """Monitor disk usage and health"""
        disk_info = {}
        try:
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info[partition.mountpoint] = {
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent
                    }
                except PermissionError:
                    continue
        except Exception as e:
            self.logger.error(f"Error checking disk health: {str(e)}")
        return disk_info

    def manage_resources(self, metrics: Dict[str, Any]):
        """Manage system resources based on current metrics"""
        try:
            # Check CPU usage
            if metrics['cpu_percent'] > CONFIG['CPU_THRESHOLD']:
                high_cpu_processes = self.identify_resource_hogs('cpu')
                self.root_bot.add_to_memory({
                    'type': 'resource_alert',
                    'resource': 'cpu',
                    'processes': high_cpu_processes
                }, long_term=True)

            # Check memory usage
            if metrics['memory_percent'] > CONFIG['MEMORY_THRESHOLD']:
                high_mem_processes = self.identify_resource_hogs('memory')
                self.root_bot.add_to_memory({
                    'type': 'resource_alert',
                    'resource': 'memory',
                    'processes': high_mem_processes
                }, long_term=True)

        except Exception as e:
            self.logger.error(f"Error in resource management: {str(e)}")

    def identify_resource_hogs(self, resource_type: str) -> List[Dict[str, Any]]:
        """Identify processes using excessive resources"""
        resource_hogs = []
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if resource_type == 'cpu' and pinfo['cpu_percent'] > 50:
                        resource_hogs.append(pinfo)
                    elif resource_type == 'memory' and pinfo['memory_percent'] > 20:
                        resource_hogs.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"Error identifying resource hogs: {str(e)}")
        return resource_hogs

    def execute_maintenance(self):
        """Perform routine system maintenance tasks"""
        try:
            # Clean old logs
            self._clean_old_logs()
            
            # Update system metrics
            metrics = self.root_bot.monitor_system()
            if metrics:
                self.manage_resources(metrics)
                
            # Check and report system health
            self._report_system_health()
            
        except Exception as e:
            self.logger.error(f"Error in maintenance execution: {str(e)}")

    def _clean_old_logs(self):
        """Clean logs older than 7 days"""
        try:
            current_time = time.time()
            log_dir = CONFIG['LOG_DIR']
            for log_file in os.listdir(log_dir):
                file_path = os.path.join(log_dir, log_file)
                if os.path.getmtime(file_path) < current_time - 7 * 86400:
                    os.remove(file_path)
        except Exception as e:
            self.logger.error(f"Error cleaning old logs: {str(e)}")

    def _report_system_health(self):
        """Generate and store system health report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'processes': self.get_process_info(),
                'services': self.get_service_status(),
                'network': self.monitor_network(),
                'disk': self.check_disk_health()
            }
            
            self.root_bot.add_to_memory({
                'type': 'health_report',
                'report': report
            }, long_term=True)
            
        except Exception as e:
            self.logger.error(f"Error generating health report: {str(e)}")
