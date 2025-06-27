"""
Automation Package for Upscale Bot
──────────────────────────────────
Contains deployment, monitoring, and automation scripts
"""

from . import log_monitor
from . import log_analyzer

__all__ = [
    'log_monitor',
    'log_analyzer'
] 