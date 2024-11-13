import os
import time
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from root_bot import RootBot, LLMInterface, TaskManager
from root_bot.config_validator import ConfigValidator
from root_bot.config.config import CONFIG

class TestRootBot(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.test_dir, 'logs')
        self.memory_dir = os.path.join(self.test_dir, 'memory')
        os.makedirs(self.log_dir)
        os.makedirs(self.memory_dir)
        
        # Patch configuration
        self.config_patcher = patch.dict('root_bot.config.config.CONFIG', {
            'LOG_DIR': self.log_dir,
            'MEMORY_DIR': self.memory_dir,
            'MONITORING_INTERVAL': 1,
            'CPU_THRESHOLD': 80,
            'MEMORY_THRESHOLD': 80,
            'DISK_THRESHOLD': 90,
            'SHORT_TERM_MEMORY_SIZE': 100,
            'LONG_TERM_MEMORY_FILE': 'test_memory.json',
            'LLAMAFILE_PATH': '/usr/local/bin/llamafile',
            'MODEL_PATH': os.path.join(self.test_dir, 'Llama-3.2-1B-Instruct.Q6_K.llamafile'),
            'LLAMAFILE_SETTINGS': {
                'ctx_size': 4096,
                'threads': os.cpu_count() or 4,
                'temp': 0.7,
                'repeat_penalty': 1.1,
                'embedding': True,
                'gpu_layers': 0
            },
            'RESOURCE_LIMITS': {
                'max_cpu_per_process': 50,
                'max_memory_per_process': 25,
                'max_disk_write_rate': 50 * 1024 * 1024
            }
        })
        self.config_patcher.start()
        
    def tearDown(self):
        """Clean up test environment"""
        self.config_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_config_validation(self):
        """Test configuration validation"""
        validator = ConfigValidator()
        is_valid, errors, warnings = validator.validate_config()
        self.assertTrue(is_valid, f"Configuration validation failed: {errors}")
        
    def test_memory_management(self):
        """Test memory management functionality"""
        bot = RootBot()
        
        # Test memory addition
        event_id = bot.add_to_memory({
            'type': 'test_event',
            'data': {'value': 1}
        }, long_term=True)
        self.assertIsNotNone(event_id)
        
        # Test memory query
        results = bot.query_memory(entry_type='test_event')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['data']['value'], 1)
        
        # Test memory deduplication
        duplicate_id = bot.add_to_memory({
            'type': 'test_event',
            'data': {'value': 1}
        }, long_term=True)
        results = bot.query_memory(entry_type='test_event')
        self.assertEqual(len(results), 1)  # Should not add duplicate
        
    def test_resource_monitoring(self):
        """Test resource monitoring capabilities"""
        bot = RootBot()
        metrics = bot.monitor_system()
        
        self.assertIsNotNone(metrics)
        self.assertIn('cpu_percent', metrics)
        self.assertIn('memory_percent', metrics)
        self.assertIn('disk_usage', metrics)
        
    def test_command_safety(self):
        """Test command safety validation"""
        bot = RootBot()
        
        # Test safe command
        self.assertTrue(bot.is_command_safe('ps aux'))
        
        # Test unsafe command
        self.assertFalse(bot.is_command_safe('rm -rf /'))
        
        # Test command with injection attempt
        self.assertFalse(bot.is_command_safe('ps aux; rm -rf /'))
        
    def test_error_handling(self):
        """Test error handling and recovery"""
        bot = RootBot()
        
        # Test invalid command execution
        success, error = bot.execute_command('invalid_command')
        self.assertFalse(success)
        self.assertIsNotNone(error)
        
        # Test timeout handling
        with patch('subprocess.Popen') as mock_popen:
            mock_popen.side_effect = TimeoutError()
            success, error = bot.execute_command('sleep 1000')
            self.assertFalse(success)
            
    def test_resource_limits(self):
        """Test resource limit enforcement"""
        bot = RootBot()
        task_manager = TaskManager(bot)
        
        # Test process resource monitoring
        processes = task_manager.get_process_info()
        for process in processes:
            self.assertLessEqual(
                process.get('cpu_percent', 0),
                CONFIG['RESOURCE_LIMITS']['max_cpu_per_process']
            )
            
    def test_llm_integration(self):
        """Test LLM integration and fallback"""
        with patch('requests.post') as mock_post:
            # Test successful LLM response
            mock_post.return_value.json.return_value = {'content': 'test response'}
            llm = LLMInterface()
            response = llm.generate_response("test prompt")
            self.assertEqual(response, 'test response')
            
            # Test LLM failure and fallback
            mock_post.side_effect = Exception("Connection failed")
            response = llm.generate_response("test prompt")
            self.assertIn("fallback", response.lower())
            
    def test_maintenance(self):
        """Test maintenance operations"""
        bot = RootBot()
        
        # Create old log file
        old_log = os.path.join(self.log_dir, 'old.log')
        with open(old_log, 'w') as f:
            f.write('test log')
        
        # Set file time to 8 days ago
        access_time = modify_time = time.time() - (8 * 24 * 60 * 60)
        os.utime(old_log, (access_time, modify_time))
        
        # Run maintenance
        bot.perform_maintenance()
        
        # Check if old log was removed
        self.assertFalse(os.path.exists(old_log))


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)

if __name__ == '__main__':
    run_tests()

