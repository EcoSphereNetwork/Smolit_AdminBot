import os
import logging
import docker
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .config.config import CONFIG

class DockerManager:
    def __init__(self):
        self.logger = logging.getLogger('RootBot.Docker')
        self.client = None
        self.api_client = None
        self._init_docker_client()

    def _init_docker_client(self) -> bool:
        """Initialize Docker client with error handling"""
        try:
            self.client = docker.from_env()
            self.api_client = docker.APIClient()
            # Test connection
            self.client.ping()
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
            return False

    def is_available(self) -> bool:
        """Check if Docker daemon is available"""
        if not self.client:
            return self._init_docker_client()
        try:
            self.client.ping()
            return True
        except:
            return False

    def _ensure_connection(self) -> bool:
        """Ensure Docker connection is available"""
        if not self.is_available():
            raise ConnectionError("Docker daemon is not available")
        return True

    def get_containers(self, all: bool = False) -> List[Dict]:
        """Get list of containers with their status"""
        self._ensure_connection()
        try:
            containers = self.client.containers.list(all=all)
            return [{
                'id': c.id,
                'name': c.name,
                'status': c.status,
                'image': c.image.tags[0] if c.image.tags else c.image.id,
                'created': c.attrs['Created'],
                'state': c.attrs['State'],
                'mounts': c.attrs['Mounts'],
                'networks': c.attrs['NetworkSettings']['Networks']
            } for c in containers]
        except Exception as e:
            self.logger.error(f"Error getting containers: {e}")
            return []

    def get_container_stats(self, container_id: str) -> Dict:
        """Get detailed stats for a container"""
        self._ensure_connection()
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)
            return {
                'cpu_percent': self._calculate_cpu_percent(stats),
                'memory_usage': stats['memory_stats'].get('usage', 0),
                'memory_limit': stats['memory_stats'].get('limit', 0),
                'network_rx': stats['networks']['eth0']['rx_bytes'] if 'networks' in stats else 0,
                'network_tx': stats['networks']['eth0']['tx_bytes'] if 'networks' in stats else 0,
                'block_read': stats['blkio_stats']['io_service_bytes_recursive'][0]['value'] if stats['blkio_stats']['io_service_bytes_recursive'] else 0,
                'block_write': stats['blkio_stats']['io_service_bytes_recursive'][1]['value'] if stats['blkio_stats']['io_service_bytes_recursive'] else 0
            }
        except Exception as e:
            self.logger.error(f"Error getting container stats: {e}")
            return {}

    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU usage percentage from stats"""
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                   stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                      stats['precpu_stats']['system_cpu_usage']
        if system_delta > 0 and cpu_delta > 0:
            return (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100.0
        return 0.0

    def start_container(self, container_id: str) -> Tuple[bool, str]:
        """Start a container"""
        self._ensure_connection()
        try:
            container = self.client.containers.get(container_id)
            container.start()
            return True, f"Container {container_id} started successfully"
        except Exception as e:
            self.logger.error(f"Error starting container {container_id}: {e}")
            return False, str(e)

    def stop_container(self, container_id: str, timeout: int = 10) -> Tuple[bool, str]:
        """Stop a container"""
        self._ensure_connection()
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            return True, f"Container {container_id} stopped successfully"
        except Exception as e:
            self.logger.error(f"Error stopping container {container_id}: {e}")
            return False, str(e)

    def remove_container(self, container_id: str, force: bool = False) -> Tuple[bool, str]:
        """Remove a container"""
        self._ensure_connection()
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            return True, f"Container {container_id} removed successfully"
        except Exception as e:
            self.logger.error(f"Error removing container {container_id}: {e}")
            return False, str(e)

    def get_images(self) -> List[Dict]:
        """Get list of images"""
        self._ensure_connection()
        try:
            images = self.client.images.list()
            return [{
                'id': img.id,
                'tags': img.tags,
                'size': img.attrs['Size'],
                'created': img.attrs['Created']
            } for img in images]
        except Exception as e:
            self.logger.error(f"Error getting images: {e}")
            return []

    def pull_image(self, image_name: str) -> Tuple[bool, str]:
        """Pull an image from registry"""
        self._ensure_connection()
        try:
            self.client.images.pull(image_name)
            return True, f"Image {image_name} pulled successfully"
        except Exception as e:
            self.logger.error(f"Error pulling image {image_name}: {e}")
            return False, str(e)

    def remove_image(self, image_id: str, force: bool = False) -> Tuple[bool, str]:
        """Remove an image"""
        self._ensure_connection()
        try:
            self.client.images.remove(image_id, force=force)
            return True, f"Image {image_id} removed successfully"
        except Exception as e:
            self.logger.error(f"Error removing image {image_id}: {e}")
            return False, str(e)

    def get_docker_info(self) -> Dict:
        """Get Docker daemon information"""
        self._ensure_connection()
        try:
            info = self.client.info()
            return {
                'containers': info['Containers'],
                'containers_running': info['ContainersRunning'],
                'containers_paused': info['ContainersPaused'],
                'containers_stopped': info['ContainersStopped'],
                'images': info['Images'],
                'driver': info['Driver'],
                'memory_limit': info['MemoryLimit'],
                'swap_limit': info['SwapLimit'],
                'kernel_version': info['KernelVersion'],
                'operating_system': info['OperatingSystem']
            }
        except Exception as e:
            self.logger.error(f"Error getting Docker info: {e}")
            return {}

