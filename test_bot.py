import time
from root_bot import RootBot, LLMInterface, TaskManager

def test_basic_functionality():
    print("Initializing RootBot...")
    bot = RootBot()
    
    print("\nTesting system monitoring...")
    metrics = bot.monitor_system()
    print(f"System Metrics: {metrics}")
    
    print("\nTesting task manager...")
    task_manager = TaskManager(bot)
    processes = task_manager.get_process_info()
    print(f"Running Processes: {len(processes)} processes found")
    
    print("\nTesting disk health check...")
    disk_info = task_manager.check_disk_health()
    print(f"Disk Info: {disk_info}")
    
    print("\nTesting network monitoring...")
    network_info = task_manager.monitor_network()
    print(f"Network Info: {network_info}")
    
    print("\nTesting memory system...")
    bot.add_to_memory({
        'type': 'test_event',
        'message': 'Testing memory system'
    }, long_term=True)
    
    print("\nShutting down bot...")
    bot.shutdown()

if __name__ == "__main__":
    test_basic_functionality()
