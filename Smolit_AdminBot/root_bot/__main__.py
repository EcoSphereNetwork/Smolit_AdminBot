import os
import sys
import signal
import daemon
import lockfile
import argparse
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
        global bot
        bot = RootBot()
        bot.llm = LLMInterface()
        bot.task_manager = TaskManager(bot)
        
        # Start the bot
        bot.run()
        
    except Exception as e:
        print(f"Error starting RootBot: {str(e)}")
        sys.exit(1)


def start_daemon():
    """Start the bot as a daemon"""
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


def stop_daemon():
    """Stop the daemon using the PID file"""
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            os.remove(PID_FILE)
            print("RootBot daemon stopped.")
        else:
            print("PID file not found. Is the daemon running?")
    except Exception as e:
        print(f"Failed to stop the daemon: {e}")


def status_daemon():
    """Check the status of the daemon"""
    if os.path.exists(PID_FILE):
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 0)
            print(f"RootBot daemon is running (PID: {pid}).")
        except OSError:
            print("PID file exists, but process is not running.")
    else:
        print("RootBot daemon is not running.")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="RootBot Daemon Control")
    parser.add_argument("--start", action="store_true", help="Start the RootBot daemon")
    parser.add_argument("--stop", action="store_true", help="Stop the RootBot daemon")
    parser.add_argument("--status", action="store_true", help="Check the status of the RootBot daemon")
    
    args = parser.parse_args()
    
    if args.start:
        start_daemon()
    elif args.stop:
        stop_daemon()
    elif args.status:
        status_daemon()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
