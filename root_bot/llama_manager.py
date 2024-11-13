import os
import sys
import stat
import logging
import requests
import subprocess
import hashlib
from typing import Tuple, Optional
from pathlib import Path
from .config.config import CONFIG

class LlamaManager:
    """Manager for LlamaFile operations and lifecycle"""
    
    LLAMAFILE_URLS = {
        'tinyllama-1.1b': 'https://huggingface.co/jartine/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf',
        'llamafile': 'https://github.com/Mozilla-Ocho/llamafile/releases/download/0.1/llamafile'
    }
    
    def __init__(self):
        self.logger = logging.getLogger('RootBot.LlamaManager')
        self.llamafile_path = CONFIG['LLAMAFILE_PATH']
        self.model_path = CONFIG['MODEL_PATH']
        self.server_process = None
        self.server_port = CONFIG.get('LLAMAFILE_PORT', 8080)
        
    def check_llamafile_available(self) -> bool:
        """Check if LlamaFile is available and executable"""
        if not os.path.exists(self.llamafile_path):
            return False
            
        # Check if file is executable
        st = os.stat(self.llamafile_path)
        return bool(st.st_mode & stat.S_IXUSR)
        
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def download_llamafile(self, force: bool = False) -> Tuple[bool, str]:
        """Download LlamaFile and set executable permissions"""
        try:
            if self.check_llamafile_available() and not force:
                return True, "LlamaFile already available"
                
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.llamafile_path), exist_ok=True)
            
            # Download LlamaFile
            self.logger.info("Downloading LlamaFile...")
            response = requests.get(self.LLAMAFILE_URLS['llamafile'], stream=True)
            response.raise_for_status()
            
            # Save with temporary name first
            temp_path = f"{self.llamafile_path}.tmp"
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            # Make executable
            os.chmod(temp_path, stat.S_IRWXU)
            
            # Move to final location
            os.rename(temp_path, self.llamafile_path)
            
            return True, "LlamaFile downloaded successfully"
            
        except Exception as e:
            self.logger.error(f"Failed to download LlamaFile: {str(e)}")
            return False, str(e)
            
    def download_model(self, force: bool = False) -> Tuple[bool, str]:
        """Download the LLM model"""
        try:
            if os.path.exists(self.model_path) and not force:
                return True, "Model already available"
                
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Download model
            self.logger.info("Downloading model...")
            response = requests.get(self.LLAMAFILE_URLS['tinyllama-1.1b'], stream=True)
            response.raise_for_status()
            
            # Save with temporary name first
            temp_path = f"{self.model_path}.tmp"
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            # Move to final location
            os.rename(temp_path, self.model_path)
            
            return True, "Model downloaded successfully"
            
        except Exception as e:
            self.logger.error(f"Failed to download model: {str(e)}")
            return False, str(e)
            
    def is_server_running(self) -> bool:
        """Check if LlamaFile server is running"""
        if self.server_process is None:
            return False
            
        return self.server_process.poll() is None
        
    def _get_server_command(self) -> list:
        """Get the command to start the server"""
        cmd = [
            self.llamafile_path,
            '--server',
            '--port', str(self.server_port),
            '--model', self.model_path,
            '--ctx-size', '2048',
            '--threads', str(os.cpu_count() or 4),
            '--embedding'  # Enable embedding API
        ]
        return cmd
        
    def start_server(self) -> Tuple[bool, str]:
        """Start the LlamaFile server"""
        try:
            if self.is_server_running():
                return True, "Server already running"
                
            if not self.check_llamafile_available():
                success, msg = self.download_llamafile()
                if not success:
                    return False, f"Failed to download LlamaFile: {msg}"
                    
            if not os.path.exists(self.model_path):
                success, msg = self.download_model()
                if not success:
                    return False, f"Failed to download model: {msg}"
                    
            # Start server process
            cmd = self._get_server_command()
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait briefly to check if process started successfully
            if self.server_process.poll() is not None:
                _, stderr = self.server_process.communicate()
                return False, f"Server failed to start: {stderr}"
                
            self.logger.info(f"LlamaFile server started on port {self.server_port}")
            return True, "Server started successfully"
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {str(e)}")
            return False, str(e)
            
    def stop_server(self) -> Tuple[bool, str]:
        """Stop the LlamaFile server"""
        try:
            if not self.is_server_running():
                return True, "Server not running"
                
            # Try graceful shutdown first
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if graceful shutdown fails
                self.server_process.kill()
                self.server_process.wait()
                
            self.server_process = None
            self.logger.info("LlamaFile server stopped")
            return True, "Server stopped successfully"
            
        except Exception as e:
            self.logger.error(f"Failed to stop server: {str(e)}")
            return False, str(e)
            
    def get_server_status(self) -> dict:
        """Get detailed server status"""
        status = {
            'running': self.is_server_running(),
            'port': self.server_port,
            'pid': self.server_process.pid if self.server_process else None,
            'llamafile_available': self.check_llamafile_available(),
            'model_available': os.path.exists(self.model_path)
        }
        
        if self.is_server_running():
            # Add resource usage info
            try:
                process = psutil.Process(self.server_process.pid)
                status.update({
                    'cpu_percent': process.cpu_percent(),
                    'memory_percent': process.memory_percent(),
                    'threads': process.num_threads(),
                    'uptime': time.time() - process.create_time()
                })
            except Exception:
                pass
                
        return status
