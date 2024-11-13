import os
import sys
import signal
from .core import RootBot
from .llm_interface import LLMInterface
from .task_manager import TaskManager

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\nShutdown signal received. Stopping RootBot...")
    if 'bot' in globals():
        bot.shutdown()
    sys.exit(0)

def main():
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
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

if __name__ == "__main__":
    main()
