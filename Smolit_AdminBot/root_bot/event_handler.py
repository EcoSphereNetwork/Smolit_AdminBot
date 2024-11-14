import os
import time
import psutil
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from typing import Callable, Dict, Optional

class SystemEventHandler:
    def __init__(self):
        self.observers: Dict[str, Observer] = {}
        self.metrics_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0
        }
        self.recovery_callbacks: Dict[str, Callable] = {}
        
    def monitor_filesystem(self, path: str, callback: Callable):
        class FSHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if not event.is_directory:
                    callback(event.src_path)

        if path not in self.observers:
            observer = Observer()
            observer.schedule(FSHandler(), path, recursive=False)
            observer.start()
            self.observers[path] = observer

    def check_system_health(self) -> Dict[str, float]:
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }

    def register_recovery_callback(self, metric: str, callback: Callable):
        self.recovery_callbacks[metric] = callback

    def handle_threshold_breach(self, metric: str, value: float):
        if metric in self.recovery_callbacks:
            self.recovery_callbacks[metric](value)

    def update_thresholds(self, new_thresholds: Dict[str, float]):
        self.metrics_thresholds.update(new_thresholds)

    def stop_monitoring(self):
        for observer in self.observers.values():
            observer.stop()
        for observer in self.observers.values():
            observer.join()
