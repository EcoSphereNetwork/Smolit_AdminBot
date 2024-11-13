import json
import logging
import time
from typing import Optional, Dict, Any, Union
from .config.config import CONFIG
from .llama_manager import LlamaManager
import requests

class LLMInterface:
    def __init__(self):
        self.logger = logging.getLogger('RootBot.LLM')
        self.llama_manager = LlamaManager()
        self.fallback_mode = False
        self.last_error_time = 0
        self.error_cooldown = 300  # 5 minutes cooldown
        self.api_url = f"http://localhost:{CONFIG['LLAMAFILE_PORT']}/completion"

    def _ensure_server_running(self) -> bool:
        """Ensure LlamaFile server is running"""
        if not self.llama_manager.is_server_running():
            success, msg = self.llama_manager.start_server()
            if not success:
                self.logger.error(f"Failed to start LlamaFile server: {msg}")
                return False
            # Wait for server to initialize
            time.sleep(5)
        return True

    def _handle_llm_error(self, error: Exception) -> None:
        """Handle LLM errors with cooldown and fallback"""
        current_time = time.time()
        if current_time - self.last_error_time > self.error_cooldown:
            self.fallback_mode = True
            self.last_error_time = current_time
            self.logger.error(f"LLM error, switching to fallback mode: {str(error)}")

    def _fallback_response(self, prompt: str) -> str:
        """Provide deterministic responses when LLM is unavailable"""
        if "analyze" in prompt.lower():
            return json.dumps({
                "status": "warning",
                "issues": ["LLM unavailable - using fallback mode"],
                "recommendations": ["Monitor system metrics", "Check logs", "Verify resources"]
            })
        return "LLM unavailable - using fallback mode"

    def generate_response(self, 
                         prompt: str, 
                         context: Optional[Dict[str, Any]] = None,
                         max_retries: int = 3,
                         timeout: int = 30) -> str:
        """Generate a response using LlamaFile server API"""
        if self.fallback_mode:
            return self._fallback_response(prompt)

        if not self._ensure_server_running():
            self._handle_llm_error(Exception("Server not available"))
            return self._fallback_response(prompt)

        for attempt in range(max_retries):
            try:
                payload = {
                    "prompt": prompt,
                    "temperature": CONFIG['LLAMAFILE_SETTINGS']['temp'],
                    "max_tokens": 500
                }
                
                if context:
                    payload["context"] = context
                
                response = requests.post(
                    self.api_url,
                    json=payload,
                    timeout=timeout
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get('content', '').strip()
                
            except Exception as e:
                self.logger.warning(f"LLM attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    self._handle_llm_error(e)
                    return self._fallback_response(prompt)
                time.sleep(1)  # Brief pause between retries

    def analyze_system_state(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system metrics with enhanced context"""
        context = {
            "previous_states": self._get_recent_states(),
            "thresholds": {
                "cpu": CONFIG['CPU_THRESHOLD'],
                "memory": CONFIG['MEMORY_THRESHOLD'],
                "disk": CONFIG['DISK_THRESHOLD']
            }
        }
        
        prompt = self._build_analysis_prompt(metrics)
        response = self.generate_response(prompt, context=context)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse LLM response as JSON")
            return {
                "status": "error",
                "issues": ["Failed to analyze system state"],
                "recommendations": ["Check system manually"]
            }

    def _get_recent_states(self) -> list:
        """Retrieve recent system states for context"""
        # TODO: Implement state history tracking
        return []

    def _build_analysis_prompt(self, metrics: Dict[str, Any]) -> str:
        """Build a detailed analysis prompt optimized for Llama 3.2"""
        return f"""<|im_start|>system
You are a system administrator analyzing server metrics. Provide detailed, actionable insights.
<|im_end|>
<|im_start|>user
Analyze these system metrics and provide recommendations:
- CPU Usage: {metrics['cpu_percent']}%
- Memory Usage: {metrics['memory_percent']}%
- Disk Usage: {metrics['disk_usage']}%
- Network Connections: {metrics['network_connections']}
- Load Average: {metrics.get('load_average', 'N/A')}
- Uptime: {metrics.get('uptime', 'N/A')} seconds

Consider:
1. Resource utilization patterns
2. Potential bottlenecks
3. Security implications
4. Performance optimization opportunities

Format your response as JSON with:
{
  "status": "normal/warning/critical",
  "issues": ["list of identified issues"],
  "recommendations": ["list of recommended actions"],
  "priority": "high/medium/low"
}
<|im_end|>
<|im_start|>assistant"""

    def evaluate_command_safety(self, command: str) -> Dict[str, Union[bool, str, list]]:
        """Enhanced command safety evaluation using Llama 3.2"""
        context = {
            "allowed_commands": CONFIG['ALLOWED_COMMANDS'],
            "blocked_commands": CONFIG['BLOCKED_COMMANDS']
        }
        
        prompt = f"""<|im_start|>system
You are a security-focused system administrator evaluating command safety. Be conservative in your assessment.
<|im_end|>
<|im_start|>user
Evaluate the safety of this system command:
{command}

Consider these aspects:
1. Potential system damage or data loss
2. Security vulnerabilities
3. Resource consumption
4. Side effects and unintended consequences
5. Privilege escalation risks

Allowed commands: {', '.join(context['allowed_commands'])}
Blocked commands: {', '.join(context['blocked_commands'])}

Format your response as JSON with:
{
  "safe": boolean,
  "risk_level": "low/medium/high",
  "concerns": ["list specific security concerns"],
  "alternatives": ["list safer alternative commands"]
}
<|im_end|>
<|im_start|>assistant"""
        
        response = self.generate_response(prompt, context=context)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "safe": False,
                "risk_level": "high",
                "concerns": ["Failed to analyze command safety"],
                "alternatives": []
            }

    def shutdown(self):
        """Cleanup and shutdown LLM interface"""
        if self.llama_manager.is_server_running():
            self.llama_manager.stop_server()

