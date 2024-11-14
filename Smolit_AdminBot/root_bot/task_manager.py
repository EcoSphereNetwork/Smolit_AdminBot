import os
import time
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import psutil
import subprocess
from collections import deque
from .config.config import CONFIG

class ResourceSnapshot:
    """Class to store and analyze system resource snapshots"""
    def __init__(self, metrics: Dict[str, Any]):
        self.timestamp = datetime.now().isoformat()
        self.metrics = metrics
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'metrics': self.metrics
        }

class TaskManager:
    def __init__(self, root_bot):
        self.root_bot = root_bot
        self.logger = logging.getLogger('RootBot.TaskManager')
        self.active_tasks = {}
        self.resource_history = deque(maxlen=100)  # Keep last 100 snapshots
        self.anomaly_threshold = 2.0  # Standard deviations for anomaly detection

    def get_process_info(self) -> List[Dict[str, Any]]:
        """Safely gather detailed information about running processes"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                          'status', 'create_time', 'num_threads', 'io_counters']):
                try:
                    pinfo = proc.info
                    # Add additional process metrics
                    pinfo['uptime'] = time.time() - pinfo['create_time']
                    if 'io_counters' in pinfo:
                        pinfo['io_rate'] = {
                            'read_bytes': pinfo['io_counters'].read_bytes,
                            'write_bytes': pinfo['io_counters'].write_bytes
                        }
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.error(f"Error gathering process info: {str(e)}")
        return processes

    def get_service_status(self) -> List[Dict[str, Any]]:
        """Get detailed status of system services with health check"""
        services = []
        try:
            cmd = "systemctl list-units --type=service --all --no-pager"
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n')[1:-7]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            service_info = {
                                'name': parts[0],
                                'status': parts[3],
                                'health': self._check_service_health(parts[0])
                            }
                            services.append(service_info)
        except Exception as e:
            self.logger.error(f"Error getting service status: {str(e)}")
        return services

    def _check_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check detailed health status of a service"""
        try:
            cmd = f"systemctl show {service_name} --property=ActiveState,SubState,LoadState"
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            if result.returncode == 0:
                health_info = {}
                for line in result.stdout.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        health_info[key] = value
                return health_info
        except Exception as e:
            self.logger.error(f"Error checking service health: {str(e)}")
        return {'status': 'unknown'}

    def monitor_network(self) -> Dict[str, Any]:
        """Enhanced network monitoring with traffic analysis"""
        network_info = {
            'interfaces': [],
            'connections': 0,
            'bytes_sent': 0,
            'bytes_recv': 0,
            'packet_stats': {},
            'connection_stats': {}
        }
        
        try:
            # Get network interface statistics
            net_io = psutil.net_io_counters(pernic=True)
            net_connections = psutil.net_connections()
            
            # Analyze network connections
            connection_types = {}
            for conn in net_connections:
                conn_type = conn.type
                connection_types[conn_type] = connection_types.get(conn_type, 0) + 1
            
            network_info['connection_stats'] = connection_types
            
            # Collect interface statistics
            for interface, stats in net_io.items():
                interface_info = {
                    'name': interface,
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv,
                    'packets_sent': stats.packets_sent,
                    'packets_recv': stats.packets_recv,
                    'errin': stats.errin,
                    'errout': stats.errout,
                    'dropin': stats.dropin,
                    'dropout': stats.dropout
                }
                network_info['interfaces'].append(interface_info)
                network_info['bytes_sent'] += stats.bytes_sent
                network_info['bytes_recv'] += stats.bytes_recv
                
            # Add connection count
            network_info['connections'] = len(net_connections)
            
        except Exception as e:
            self.logger.error(f"Error monitoring network: {str(e)}")
            
        return network_info

    def check_disk_health(self) -> Dict[str, Any]:
        """Enhanced disk health monitoring"""
        disk_info = {}
        try:
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    # Get disk I/O statistics
                    io_stats = psutil.disk_io_counters(perdisk=True)
                    
                    disk_info[partition.mountpoint] = {
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent,
                        'filesystem': partition.fstype,
                        'device': partition.device,
                        'io_stats': io_stats.get(partition.device, {})
                    }
                    
                    # Check for disk health issues
                    if usage.percent > CONFIG['DISK_THRESHOLD']:
                        self.logger.warning(f"High disk usage on {partition.mountpoint}: {usage.percent}%")
                        
                except PermissionError:
                    continue
        except Exception as e:
            self.logger.error(f"Error checking disk health: {str(e)}")
        return disk_info

    def detect_anomalies(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect system anomalies using statistical analysis"""
        anomalies = []
        
        # Add current metrics to history
        self.resource_history.append(ResourceSnapshot(metrics))
        
        if len(self.resource_history) > 10:  # Need enough data points
            # Calculate mean and standard deviation for key metrics
            cpu_values = [s.metrics['cpu_percent'] for s in self.resource_history]
            mem_values = [s.metrics['memory_percent'] for s in self.resource_history]
            
            cpu_mean = sum(cpu_values) / len(cpu_values)
            mem_mean = sum(mem_values) / len(mem_values)
            
            cpu_std = (sum((x - cpu_mean) ** 2 for x in cpu_values) / len(cpu_values)) ** 0.5
            mem_std = (sum((x - mem_mean) ** 2 for x in mem_values) / len(mem_values)) ** 0.5
            
            # Check for anomalies
            if abs(metrics['cpu_percent'] - cpu_mean) > self.anomaly_threshold * cpu_std:
                anomalies.append({
                    'type': 'cpu',
                    'value': metrics['cpu_percent'],
                    'threshold': cpu_mean + self.anomaly_threshold * cpu_std
                })
                
            if abs(metrics['memory_percent'] - mem_mean) > self.anomaly_threshold * mem_std:
                anomalies.append({
                    'type': 'memory',
                    'value': metrics['memory_percent'],
                    'threshold': mem_mean + self.anomaly_threshold * mem_std
                })
                
        return anomalies

    def manage_resources(self, metrics: Dict[str, Any]):
        """Enhanced resource management with predictive analysis"""
        try:
            # Detect anomalies
            anomalies = self.detect_anomalies(metrics)
            
            # Check CPU usage
            if metrics['cpu_percent'] > CONFIG['CPU_THRESHOLD']:
                high_cpu_processes = self.identify_resource_hogs('cpu')
                self.root_bot.add_to_memory({
                    'type': 'resource_alert',
                    'resource': 'cpu',
                    'processes': high_cpu_processes,
                    'anomalies': [a for a in anomalies if a['type'] == 'cpu']
                }, long_term=True)

            # Check memory usage
            if metrics['memory_percent'] > CONFIG['MEMORY_THRESHOLD']:
                high_mem_processes = self.identify_resource_hogs('memory')
                self.root_bot.add_to_memory({
                    'type': 'resource_alert',
                    'resource': 'memory',
                    'processes': high_mem_processes,
                    'anomalies': [a for a in anomalies if a['type'] == 'memory']
                }, long_term=True)

            # Store resource snapshot
            self._store_resource_snapshot(metrics)

        except Exception as e:
            self.logger.error(f"Error in resource management: {str(e)}")

    def _store_resource_snapshot(self, metrics: Dict[str, Any]):
        """Store resource usage snapshot for trend analysis"""
        snapshot = ResourceSnapshot(metrics)
        self.resource_history.append(snapshot)
        
        # Save to disk periodically
        self._save_resource_history()

    def _save_resource_history(self):
        """Save resource history to disk"""
        try:
            history_file = os.path.join(CONFIG['MEMORY_DIR'], 'resource_history.json')
            history_data = [s.to_dict() for s in self.resource_history]
            
            with open(history_file, 'w') as f:
                json.dump(history_data, f)
                
        except Exception as e:
            self.logger.error(f"Error saving resource history: {str(e)}")

    def identify_resource_hogs(self, resource_type: str) -> List[Dict[str, Any]]:
        """Enhanced resource hog identification with detailed analysis"""
        resource_hogs = []
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                          'num_threads', 'io_counters', 'create_time']):
                try:
                    pinfo = proc.info
                    pinfo['uptime'] = time.time() - pinfo['create_time']
                    
                    # Add IO rates if available
                    if hasattr(proc, 'io_counters'):
                        io = proc.io_counters()
                        pinfo['io_rate'] = {
                            'read_bytes': io.read_bytes,
                            'write_bytes': io.write_bytes
                        }
                    
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

