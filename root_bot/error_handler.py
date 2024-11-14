import logging
import traceback
from typing import Optional, Type, Dict, Any
from datetime import datetime

class RootBotError(Exception):
    """Base exception class for RootBot"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()

class ConfigError(RootBotError):
    """Raised for configuration-related errors"""
    pass

class MemoryError(RootBotError):
    """Raised for memory-related errors"""
    pass

class TaskError(RootBotError):
    """Raised for task-related errors"""
    pass

class ErrorHandler:
    """Centralized error handling for RootBot"""
    
    def __init__(self):
        self.logger = logging.getLogger('RootBot.error')
        self.error_counts: Dict[str, int] = {}
        
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Handle an error with proper logging and recovery actions"""
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        error_info = {
            'type': error_type,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'count': self.error_counts[error_type],
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }
        
        if isinstance(error, RootBotError):
            error_info.update(error.details)
        
        # Log the error with all available context
        self.logger.error(
            f"Error occurred: {error_type}",
            extra=error_info
        )
        
        # Implement recovery actions based on error type
        self._handle_specific_error(error, error_info)
        
    def _handle_specific_error(self, error: Exception, error_info: Dict[str, Any]) -> None:
        """Implement specific recovery actions for different error types"""
        if isinstance(error, ConfigError):
            self.logger.info("Attempting to reload configuration...")
            # Configuration reload logic would go here
            
        elif isinstance(error, MemoryError):
            self.logger.info("Attempting to recover memory state...")
            # Memory recovery logic would go here
            
        elif isinstance(error, TaskError):
            self.logger.info("Attempting to recover task state...")
            # Task recovery logic would go here
            
        # Add more specific error handlers as needed
        
    def get_error_stats(self) -> Dict[str, Any]:
        """Get statistics about errors that have occurred"""
        return {
            'counts': self.error_counts.copy(),
            'total': sum(self.error_counts.values()),
            'types': list(self.error_counts.keys())
        }
