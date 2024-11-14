import os
import json
import logging
import time
import subprocess
from typing import Optional, Dict, Any, Union
from .config.config import CONFIG
import requests
from transformers import AutoModelForCausalLM, AutoTokenizer
from .retry_utils import retry_with_backoff, RetryError

class LLMError(Exception):
    """Base exception for LLM-related errors"""
    pass

class LLMConnectionError(LLMError):
    """Raised when connection to LLM fails"""
    pass

class LLMGenerationError(LLMError):
    """Raised when text generation fails"""
    pass

class LLMInterface:
    def __init__(self, model_name="Mozilla/Llama-3.2-1B-Instruct"):
        self.logger = logging.getLogger('RootBot.llm')
        self._load_model(model_name)
        self.fallback_mode = False
        self.last_error_time = 0
        self.error_cooldown = 300  # 5 minutes cooldown

    @retry_with_backoff(
        max_retries=3,
        initial_delay=1.0,
        max_delay=10.0,
        exceptions=(Exception,)
    )
    def _load_model(self, model_name: str) -> None:
        """Load the LLM model with retry mechanism"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            self.logger.info(f"Successfully loaded model: {model_name}")
        except Exception as e:
            self.logger.error(f"Failed to load model: {str(e)}")
            raise LLMConnectionError(f"Failed to load model {model_name}: {str(e)}")

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

    @retry_with_backoff(
        max_retries=2,
        initial_delay=0.5,
        max_delay=5.0,
        exceptions=(Exception,)
    )
    def generate_response(self, prompt: str, max_length: int = 50) -> str:
        """Generate response with retry mechanism"""
        if self.fallback_mode:
            return self._fallback_response(prompt)

        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=max_length,
                num_return_sequences=1,
                no_repeat_ngram_size=2
            )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            self.logger.info(
                "Generated response",
                extra={
                    'prompt_length': len(prompt),
                    'response_length': len(response)
                }
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to generate response: {str(e)}")
            raise LLMGenerationError(f"Failed to generate response: {str(e)}")

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
        response = self.generate_response(prompt)
        
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
        
        response = self.generate_response(prompt)
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
        """Shutdown the LLM server"""
        if hasattr(self, 'process') and self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

