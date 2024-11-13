import subprocess
import json
import logging
from typing import Optional, Dict, Any
from .config.config import CONFIG

class LLMInterface:
    def __init__(self):
        self.logger = logging.getLogger('RootBot.LLM')
        self.model_path = CONFIG['MODEL_PATH']
        self.llamafile_path = CONFIG['LLAMAFILE_PATH']

    def generate_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate a response using the Llamafile model"""
        try:
            # Prepare the command to run llamafile
            cmd = [
                self.llamafile_path,
                '-m', self.model_path,
                '--temp', '0.7',
                '--ctx-size', '2048',
                '-p', prompt
            ]
            
            # Run the model
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            output, error = process.communicate(timeout=30)
            
            if process.returncode != 0:
                self.logger.error(f"LLM error: {error}")
                return ""
                
            return output.strip()
            
        except subprocess.TimeoutExpired:
            process.kill()
            self.logger.error("LLM response generation timed out")
            return ""
        except Exception as e:
            self.logger.error(f"LLM generation error: {str(e)}")
            return ""

    def analyze_system_state(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system metrics and generate recommendations"""
        prompt = f"""
        Analyze these system metrics and provide recommendations:
        CPU Usage: {metrics['cpu_percent']}%
        Memory Usage: {metrics['memory_percent']}%
        Disk Usage: {metrics['disk_usage']}%
        Network Connections: {metrics['network_connections']}
        
        Provide analysis in JSON format with fields:
        - status: overall system status (normal/warning/critical)
        - issues: list of identified issues
        - recommendations: list of recommended actions
        """
        
        response = self.generate_response(prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse LLM response as JSON")
            return {
                "status": "error",
                "issues": ["Failed to analyze system state"],
                "recommendations": []
            }

    def evaluate_command_safety(self, command: str) -> bool:
        """Use LLM to evaluate if a command is safe to execute"""
        prompt = f"""
        Evaluate if this system command is safe to execute:
        {command}
        
        Respond with only 'safe' or 'unsafe'.
        Consider potential system damage, data loss, or security risks.
        """
        
        response = self.generate_response(prompt).lower().strip()
        return response == 'safe'
