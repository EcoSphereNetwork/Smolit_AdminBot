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
    @patch('root_bot.core.LLMInterface')
    def setUp(self, mock_llm):
        """Set up test environment"""
        # Mock LLM interface
        mock_llm.return_value.generate_response.return_value = "test response"
        mock_llm.return_value._ensure_server_running.return_value = True
        
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
        
    @patch('root_bot.core.LLMInterface')
    def test_memory_management(self, mock_llm):
        """Test memory management functionality"""
        mock_llm.return_value.generate_response.return_value = "test response"
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

    @patch('root_bot.core.LLMInterface')
    def test_resource_monitoring(self, mock_llm):
        """Test resource monitoring capabilities"""
        mock_llm.return_value.generate_response.return_value = "test response"
        bot = RootBot()
        metrics = bot.monitor_system()
        
        self.assertIsNotNone(metrics)
        self.assertIn('cpu_percent', metrics)
        self.assertIn('memory_percent', metrics)
        self.assertIn('disk_usage', metrics)

    @patch('root_bot.core.LLMInterface')
    def test_command_safety(self, mock_llm):
        """Test command safety validation"""
        mock_llm.return_value.generate_response.return_value = "test response"
        bot = RootBot()
        
        # Test safe command
        self.assertTrue(bot.is_command_safe('ps aux'))
        
        # Test unsafe command
        self.assertFalse(bot.is_command_safe('rm -rf /'))
        
        # Test command with injection attempt
        self.assertFalse(bot.is_command_safe('ps aux; rm -rf /'))

if __name__ == '__main__':
    unittest.main()
