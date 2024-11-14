import os
import time
import logging
from typing import Dict, Set, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
from .error_handler import RootBotError

class FSMonitorError(RootBotError):
    """Raised for file system monitoring errors"""
    pass

class ConfigChangeHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str], None]):
        self.logger = logging.getLogger('RootBot.fsmonitor')
        self.callback = callback
        
    def on_modified(self, event):
        if isinstance(event, FileModifiedEvent):
            if event.src_path.endswith('config.py') or event.src_path.endswith('rootbot.conf'):
                self.logger.info(f"Configuration file modified: {event.src_path}")
                self.callback(event.src_path)

class FileSystemMonitor:
    """Monitors file system events and triggers appropriate actions"""
    
    def __init__(self, config: Dict[str, str]):
        self.logger = logging.getLogger('RootBot.fsmonitor')
        self.config = config
        self.observer = Observer()
        self.watched_paths: Set[str] = set()
        self.handlers: Dict[str, FileSystemEventHandler] = {}
        
    def start(self) -> None:
        """Start the file system monitor"""
        try:
            self.observer.start()
            self.logger.info("File system monitor started")
        except Exception as e:
            raise FSMonitorError("Failed to start file system monitor", {'error': str(e)})
            
    def stop(self) -> None:
        """Stop the file system monitor"""
        try:
            self.observer.stop()
            self.observer.join()
            self.logger.info("File system monitor stopped")
        except Exception as e:
            self.logger.error(f"Error stopping file system monitor: {str(e)}")
            
    def watch_config(self, config_dir: str, callback: Callable[[str], None]) -> None:
        """Watch configuration directory for changes"""
        try:
            handler = ConfigChangeHandler(callback)
            self.observer.schedule(handler, config_dir, recursive=False)
            self.watched_paths.add(config_dir)
            self.handlers[config_dir] = handler
            self.logger.info(f"Watching configuration directory: {config_dir}")
        except Exception as e:
            raise FSMonitorError(
                "Failed to set up config monitoring",
                {'directory': config_dir, 'error': str(e)}
            )
            
    def watch_directory(self, 
                       path: str,
                       handler: FileSystemEventHandler,
                       recursive: bool = False) -> None:
        """Watch a directory with a custom event handler"""
        try:
            self.observer.schedule(handler, path, recursive=recursive)
            self.watched_paths.add(path)
            self.handlers[path] = handler
            self.logger.info(
                f"Watching directory: {path}",
                extra={'recursive': recursive}
            )
        except Exception as e:
            raise FSMonitorError(
                "Failed to set up directory monitoring",
                {'directory': path, 'error': str(e)}
            )
            
    def is_watching(self, path: str) -> bool:
        """Check if a path is being watched"""
        return path in self.watched_paths
        
    def get_watch_status(self) -> Dict[str, bool]:
        """Get status of all watched paths"""
        return {
            path: self.observer.is_alive() for path in self.watched_paths
        }
