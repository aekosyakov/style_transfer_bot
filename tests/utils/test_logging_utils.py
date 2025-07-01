"""Unit tests for logging utilities."""

import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from src.utils.logging_utils import (
    setup_logging, 
    generate_request_id, 
    log_user_action, 
    log_api_call, 
    log_processing_step,
    get_logger
)

def test_generate_request_id():
    """Test request ID generation format and uniqueness."""
    req_id1 = generate_request_id()
    req_id2 = generate_request_id()
    
    # Should start with "req_"
    assert req_id1.startswith("req_")
    assert req_id2.startswith("req_")
    
    # Should be unique
    assert req_id1 != req_id2
    
    # Should have expected format: req_timestamp_hash
    parts = req_id1.split("_")
    assert len(parts) == 3
    assert parts[0] == "req"
    assert parts[1].isdigit()  # timestamp
    assert len(parts[2]) == 8  # 8-char hash

def test_setup_logging():
    """Test logging setup functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('src.utils.logging_utils.os.makedirs') as mock_makedirs:
            logger = setup_logging()
            
            assert logger is not None
            assert logger.name == "src.utils.logging_utils"
            mock_makedirs.assert_called_once_with('logs', exist_ok=True)

def test_setup_logging_with_directory_creation_failure():
    """Test logging setup when directory creation fails."""
    with patch('src.utils.logging_utils.os.makedirs', side_effect=OSError("Permission denied")):
        with patch('builtins.print') as mock_print:
            logger = setup_logging()
            
            assert logger is not None
            mock_print.assert_any_call("Warning: Could not create log file handler: Permission denied")
            mock_print.assert_any_call("Logging to console only.")

def test_log_user_action():
    """Test user action logging."""
    mock_logger = MagicMock()
    
    with patch('src.utils.logging_utils.logger', mock_logger):
        log_user_action(
            user_id=12345, 
            action="test_action",
            details={"key": "value"}, 
            request_id="test_req_123"
        )
        
        # Verify logger.info was called
        mock_logger.info.assert_called_once()
        
        # Check the logged data structure
        call_args = mock_logger.info.call_args[0][0]
        assert "👤 USER_ACTION:" in call_args
        
        # Parse the JSON data
        json_str = call_args.split("👤 USER_ACTION: ")[1]
        log_data = json.loads(json_str)
        
        assert log_data["user_id"] == 12345
        assert log_data["action"] == "test_action"
        assert log_data["request_id"] == "test_req_123"
        assert log_data["details"] == {"key": "value"}
        assert "timestamp" in log_data

def test_log_user_action_auto_request_id():
    """Test user action logging with auto-generated request ID."""
    mock_logger = MagicMock()
    
    with patch('src.utils.logging_utils.logger', mock_logger):
        log_user_action(user_id=12345, action="test_action")
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        json_str = call_args.split("👤 USER_ACTION: ")[1]
        log_data = json.loads(json_str)
        
        # Should have auto-generated request ID
        assert log_data["request_id"].startswith("req_")
        assert log_data["details"] == {}

def test_log_api_call_success():
    """Test API call logging for successful calls."""
    mock_logger = MagicMock()
    
    with patch('src.utils.logging_utils.logger', mock_logger):
        log_api_call(
            api_name="test_api",
            request_id="test_req_123", 
            user_id=12345,
            params={"param1": "value1"},
            duration=1.5,
            success=True,
            error=None
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "🌐 API_SUCCESS:" in call_args
        
        json_str = call_args.split("🌐 API_SUCCESS: ")[1]
        log_data = json.loads(json_str)
        
        assert log_data["api"] == "test_api"
        assert log_data["success"] is True
        assert log_data["duration_seconds"] == 1.5
        assert log_data["error"] is None

def test_log_api_call_failure():
    """Test API call logging for failed calls."""
    mock_logger = MagicMock()
    
    with patch('src.utils.logging_utils.logger', mock_logger):
        log_api_call(
            api_name="test_api",
            request_id="test_req_123",
            user_id=12345, 
            params={"param1": "value1"},
            duration=2.0,
            success=False,
            error="Connection timeout"
        )
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "🌐 API_FAILURE:" in call_args
        
        json_str = call_args.split("🌐 API_FAILURE: ")[1]
        log_data = json.loads(json_str)
        
        assert log_data["success"] is False
        assert log_data["error"] == "Connection timeout"

def test_log_processing_step_success():
    """Test processing step logging for successful steps."""
    mock_logger = MagicMock()
    
    with patch('src.utils.logging_utils.logger', mock_logger):
        log_processing_step(
            step="image_processing",
            request_id="test_req_123",
            user_id=12345,
            details={"step_data": "value"},
            success=True
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "⚙️  PROCESSING:" in call_args
        
        json_str = call_args.split("⚙️  PROCESSING: ")[1]
        log_data = json.loads(json_str)
        
        assert log_data["step"] == "image_processing"
        assert log_data["success"] is True
        assert log_data["error"] is None

def test_log_processing_step_failure():
    """Test processing step logging for failed steps."""
    mock_logger = MagicMock()
    
    with patch('src.utils.logging_utils.logger', mock_logger):
        log_processing_step(
            step="image_processing",
            request_id="test_req_123", 
            user_id=12345,
            details={"step_data": "value"},
            success=False,
            error="Processing failed"
        )
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "⚙️  PROCESSING_ERROR:" in call_args
        
        json_str = call_args.split("⚙️  PROCESSING_ERROR: ")[1]
        log_data = json.loads(json_str)
        
        assert log_data["success"] is False
        assert log_data["error"] == "Processing failed"

def test_get_logger():
    """Test get_logger function."""
    # Reset the global logger
    import src.utils.logging_utils as logging_utils
    logging_utils.logger = None
    
    logger = get_logger()
    assert logger is not None
    
    # Should return the same logger on subsequent calls
    logger2 = get_logger()
    assert logger is logger2

def test_logging_functions_auto_initialize():
    """Test that logging functions auto-initialize logger when None."""
    import src.utils.logging_utils as logging_utils
    
    # Reset logger to None
    logging_utils.logger = None
    
    with patch.object(logging_utils, 'setup_logging') as mock_setup:
        mock_setup.return_value = MagicMock()
        
        log_user_action(12345, "test")
        mock_setup.assert_called_once()
        
    # Reset and test other functions
    logging_utils.logger = None
    with patch.object(logging_utils, 'setup_logging') as mock_setup:
        mock_setup.return_value = MagicMock()
        
        log_api_call("api", "req", 123, {}, success=True)
        mock_setup.assert_called_once()
        
    logging_utils.logger = None
    with patch.object(logging_utils, 'setup_logging') as mock_setup:
        mock_setup.return_value = MagicMock()
        
        log_processing_step("step", "req", 123)
        mock_setup.assert_called_once() 