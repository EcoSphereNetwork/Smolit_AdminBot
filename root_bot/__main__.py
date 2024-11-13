import os
import sys
import signal
import daemon
import lockfile
from .core import RootBot
from .llm_interface import LLMInterface
from .task_manager import TaskManager
from .config.config import CONFIG

PID_FILE = '/var/run/rootbot.pid'
LOG_FILE = os.path.join(CONFIG['LOG_DIR'], 'rootbot.log')

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    if 'bot' in globals():
        bot.shutdown()
    sys.exit(0)

def setup_daemon_context():
    """Set up the daemon context"""
    return daemon.DaemonContext(
        working_directory='/opt/rootbot',
        umask=0o022,
        pidfile=lockfile.FileLock(PID_FILE),
        files_preserve=[
            # Keep log file descriptors
            open(LOG_FILE, 'a').fileno()
        ],
        signal_map={
            signal.SIGTERM: signal_handler,
            signal.SIGINT: signal_handler
        }
    )

def run_bot():
    """Run the bot with proper initialization"""
    try:
        # Initialize the bot and its components
        bot = RootBot()
        bot.llm = LLMInterface()
        bot.task_manager = TaskManager(bot)
        
        # Start the bot
        bot.run()
        
    except Exception as e:
        print(f"Error starting RootBot: {str(e)}")
        sys.exit(1)

def main():
    """Main entry point"""
    if os.geteuid() != 0:
        sys.exit("This program must be run as root")
        
    # Create required directories
    os.makedirs(CONFIG['LOG_DIR'], exist_ok=True)
    os.makedirs(CONFIG['MEMORY_DIR'], exist_ok=True)
    
    # Set up daemon context
    context = setup_daemon_context()
    
    # Run as daemon
    with context:
        run_bot()

if __name__ == "__main__":
    main()

