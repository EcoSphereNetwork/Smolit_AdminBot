import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['module'] = record.module
        log_record['process_id'] = record.process
        if hasattr(record, 'telemetry'):
            log_record['telemetry'] = record.telemetry
        if hasattr(record, 'security'):
            log_record['security'] = record.security

def setup_logging(log_dir: str = 'logs') -> None:
    """Configure structured JSON logging with separate streams for different concerns"""
    os.makedirs(log_dir, exist_ok=True)
    
    # Base formatter
    json_formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    
    # Main application log
    app_handler = logging.FileHandler(
        os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.json')
    )
    app_handler.setFormatter(json_formatter)
    
    # Security events log
    security_handler = logging.FileHandler(
        os.path.join(log_dir, f'security_{datetime.now().strftime("%Y%m%d")}.json')
    )
    security_handler.setFormatter(json_formatter)
    
    # Telemetry log
    telemetry_handler = logging.FileHandler(
        os.path.join(log_dir, f'telemetry_{datetime.now().strftime("%Y%m%d")}.json')
    )
    telemetry_handler.setFormatter(json_formatter)
    
    # Console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    
    # Root logger setup
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(console_handler)
    
    # Security logger setup
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.INFO)
    security_logger.addHandler(security_handler)
    
    # Telemetry logger setup
    telemetry_logger = logging.getLogger('telemetry')
    telemetry_logger.setLevel(logging.INFO)
    telemetry_logger.addHandler(telemetry_handler)
