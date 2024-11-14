"""
RootBot - An autonomous system administration bot
"""

__version__ = '0.1.0'
__author__ = 'RootBot Team'

from .core import RootBot
from .llm_interface import LLMInterface
from .task_manager import TaskManager

__all__ = ['RootBot', 'LLMInterface', 'TaskManager']
