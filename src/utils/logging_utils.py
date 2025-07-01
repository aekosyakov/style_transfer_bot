"""Logging utilities for the bot - standalone helper functions."""

import os
import sys
import json
import time
import uuid
import logging
from typing import Dict, Any
from datetime import datetime

# Global logger - will be set by setup_logging()
logger = None

def setup_logging():
    """Setup logging with safe file handler that creates directory if needed."""
    global logger
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Try to create file handler, but don't fail if logs directory doesn't exist
    try:
        os.makedirs('logs', exist_ok=True)
        handlers.append(logging.FileHandler('logs/bot.log'))
    except Exception as e:
        print(f"Warning: Could not create log file handler: {e}")
        print("Logging to console only.")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
        handlers=handlers
    )
    
    logger = logging.getLogger(__name__)
    return logger

def generate_request_id() -> str:
    """Generate unique request ID for tracing."""
    return f"req_{int(time.time())}_{uuid.uuid4().hex[:8]}"

def log_user_action(user_id: int, action: str, details: Dict[str, Any] = None, request_id: str = None):
    """Log user action with context."""
    current_logger = get_logger()
    
    log_data = {
        "user_id": user_id,
        "action": action,
        "request_id": request_id or generate_request_id(),
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    current_logger.info(f"👤 USER_ACTION: {json.dumps(log_data)}")

def log_api_call(api_name: str, request_id: str, user_id: int, params: Dict[str, Any], 
                 duration: float = None, success: bool = None, error: str = None):
    """Log API call with timing and result information."""
    current_logger = get_logger()
    
    log_data = {
        "api": api_name,
        "request_id": request_id,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "params": params,
        "duration_seconds": duration,
        "success": success,
        "error": error
    }
    if success:
        current_logger.info(f"🌐 API_SUCCESS: {json.dumps(log_data)}")
    else:
        current_logger.error(f"🌐 API_FAILURE: {json.dumps(log_data)}")

def log_processing_step(step: str, request_id: str, user_id: int, details: Dict[str, Any] = None, 
                       success: bool = True, error: str = None):
    """Log processing step with context."""
    current_logger = get_logger()
    
    log_data = {
        "step": step,
        "request_id": request_id,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "details": details or {},
        "error": error
    }
    if success:
        current_logger.info(f"⚙️  PROCESSING: {json.dumps(log_data)}")
    else:
        current_logger.error(f"⚙️  PROCESSING_ERROR: {json.dumps(log_data)}")

def get_logger():
    """Get the global logger, initializing if needed."""
    global logger
    if logger is None:
        logger = setup_logging()
    return logger 