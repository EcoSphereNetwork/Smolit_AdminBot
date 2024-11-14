#!/usr/bin/env python3

import os
import sys
import time
import signal
import logging
import subprocess
from datetime import datetime
from root_bot.process_monitor import ProcessMonitor

class Watchdog:
    def __init__(self):
        self.setup_logging()
        self.process_monitor = ProcessMonitor()
        self.bot_process = None
        self.running = True
        
    def setup_logging(self):
        """Configure logging for watchdog"""
        log_file = os.path.join('logs', f'watchdog_{datetime.now().strftime("%Y%m%d")}.log')
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='{"timestamp":"%(asctime)s","level":"%(levelname)s","component":"watchdog","message":"%(message)s"}',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('Watchdog')
        
    def start_bot(self):
        """Start the RootBot process"""
        try:
            self.bot_process = subprocess.Popen(
                ['python3', '-m', 'root_bot'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.logger.info(f"Started RootBot with PID {self.bot_process.pid}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start RootBot: {str(e)}")
            return False
            
    def monitor(self):
        """Main monitoring loop"""
        self.logger.info("Starting watchdog monitor")
        
        while self.running:
            if not self.process_monitor.is_process_running():
                self.logger.warning("RootBot process not running, attempting restart")
                if self.start_bot():
                    time.sleep(5)  # Wait for process to initialize
                else:
                    time.sleep(30)  # Wait longer before retry if start failed
                continue
                
            if not self.process_monitor.check_health():
                self.logger.warning("RootBot health check failed, restarting")
                self.restart_bot()
                
            time.sleep(10)  # Check interval
            
    def restart_bot(self):
        """Restart the RootBot process"""
        try:
            pid = self.process_monitor.read_pid()
            if pid:
                os.kill(pid, signal.SIGTERM)
                time.sleep(5)  # Wait for graceful shutdown
                
            if self.process_monitor.is_process_running():
                self.logger.warning("Force killing RootBot process")
                os.kill(pid, signal.SIGKILL)
                
            self.start_bot()
            
        except Exception as e:
            self.logger.error(f"Failed to restart RootBot: {str(e)}")
            
    def cleanup(self, signum=None, frame=None):
        """Clean up resources"""
        self.logger.info("Shutting down watchdog")
        self.running = False
        
        if self.bot_process:
            self.bot_process.terminate()
            self.bot_process.wait(timeout=5)
            
        self.process_monitor.cleanup()
        
    def run(self):
        """Run the watchdog"""
        signal.signal(signal.SIGTERM, self.cleanup)
        signal.signal(signal.SIGINT, self.cleanup)
        
        try:
            self.monitor()
        except KeyboardInterrupt:
            self.cleanup()
        except Exception as e:
            self.logger.error(f"Watchdog error: {str(e)}")
            self.cleanup()
            
if __name__ == '__main__':
    watchdog = Watchdog()
    watchdog.run()
