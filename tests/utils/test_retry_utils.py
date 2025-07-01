"""Unit tests for retry utilities."""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from telegram.error import TimedOut, NetworkError, RetryAfter
from src.utils.retry_utils import retry_telegram_request, get_retry_logger

@pytest.mark.asyncio
async def test_retry_telegram_request_success_first_try():
    """Test successful operation on first try."""
    mock_operation = AsyncMock(return_value="success")
    
    result = await retry_telegram_request(mock_operation)
    
    assert result == "success"
    assert mock_operation.call_count == 1

@pytest.mark.asyncio 
async def test_retry_telegram_request_success_after_retry():
    """Test successful operation after retries."""
    mock_operation = AsyncMock()
    mock_operation.side_effect = [TimedOut("timeout"), "success"]
    
    with patch('src.utils.retry_utils.asyncio.sleep') as mock_sleep:
        result = await retry_telegram_request(mock_operation, max_retries=2)
    
    assert result == "success"
    assert mock_operation.call_count == 2
    mock_sleep.assert_called_once_with(1.0)  # Initial delay

@pytest.mark.asyncio
async def test_retry_telegram_request_timeout_all_retries():
    """Test operation that times out on all retries."""
    mock_operation = AsyncMock()
    mock_operation.side_effect = TimedOut("persistent timeout")
    
    with patch('src.utils.retry_utils.asyncio.sleep'):
        with pytest.raises(TimedOut):
            await retry_telegram_request(mock_operation, max_retries=2)
    
    assert mock_operation.call_count == 3  # Initial + 2 retries

@pytest.mark.asyncio
async def test_retry_telegram_request_network_error():
    """Test network error handling."""
    mock_operation = AsyncMock()
    mock_operation.side_effect = NetworkError("network issue")
    
    with patch('src.utils.retry_utils.asyncio.sleep'):
        with pytest.raises(NetworkError):
            await retry_telegram_request(mock_operation, max_retries=1)
    
    assert mock_operation.call_count == 2  # Initial + 1 retry

@pytest.mark.asyncio
async def test_retry_telegram_request_rate_limit():
    """Test RetryAfter (rate limit) handling."""
    mock_operation = AsyncMock()
    mock_operation.side_effect = [RetryAfter(5), "success"]
    
    with patch('src.utils.retry_utils.asyncio.sleep') as mock_sleep:
        result = await retry_telegram_request(mock_operation, max_retries=1)
    
    assert result == "success"
    assert mock_operation.call_count == 2
    mock_sleep.assert_called_once_with(6)  # retry_after + 1 second buffer

@pytest.mark.asyncio
async def test_retry_telegram_request_rate_limit_exceeded():
    """Test rate limit exceeded after all retries."""
    mock_operation = AsyncMock()
    mock_operation.side_effect = RetryAfter(5)
    
    with patch('src.utils.retry_utils.asyncio.sleep'):
        with pytest.raises(RetryAfter):
            await retry_telegram_request(mock_operation, max_retries=1)
    
    assert mock_operation.call_count == 2

@pytest.mark.asyncio
async def test_retry_telegram_request_non_retryable_error():
    """Test non-retryable errors are raised immediately."""
    mock_operation = AsyncMock()
    mock_operation.side_effect = ValueError("bad value")
    
    with pytest.raises(ValueError):
        await retry_telegram_request(mock_operation, max_retries=3)
    
    assert mock_operation.call_count == 1  # No retries for non-retryable errors

@pytest.mark.asyncio
async def test_retry_telegram_request_exponential_backoff():
    """Test exponential backoff delays."""
    mock_operation = AsyncMock()
    mock_operation.side_effect = [
        TimedOut("timeout1"), 
        TimedOut("timeout2"), 
        TimedOut("timeout3"),
        "success"
    ]
    
    with patch('src.utils.retry_utils.asyncio.sleep') as mock_sleep:
        result = await retry_telegram_request(mock_operation, max_retries=3, initial_delay=2.0)
    
    assert result == "success"
    assert mock_operation.call_count == 4
    
    # Check exponential backoff: 2.0, 4.0, 8.0
    expected_delays = [2.0, 4.0, 8.0]
    actual_delays = [call.args[0] for call in mock_sleep.call_args_list]
    assert actual_delays == expected_delays

@pytest.mark.asyncio
async def test_retry_telegram_request_custom_parameters():
    """Test custom retry parameters."""
    mock_operation = AsyncMock()
    mock_operation.side_effect = [TimedOut("timeout"), "success"]
    
    with patch('src.utils.retry_utils.asyncio.sleep') as mock_sleep:
        result = await retry_telegram_request(
            mock_operation, 
            max_retries=1, 
            initial_delay=0.5
        )
    
    assert result == "success"
    mock_sleep.assert_called_once_with(0.5)

@pytest.mark.asyncio
async def test_retry_telegram_request_logging():
    """Test that retry operations are properly logged."""
    mock_operation = AsyncMock()
    mock_operation.side_effect = [TimedOut("timeout"), "success"]
    
    with patch('src.utils.retry_utils.get_retry_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        with patch('src.utils.retry_utils.asyncio.sleep'):
            result = await retry_telegram_request(mock_operation)
    
    assert result == "success"
    
    # Verify logging calls
    assert mock_logger.warning.call_count == 1
    assert mock_logger.info.call_count == 1
    
    # Check log message content
    warning_call = mock_logger.warning.call_args[0][0]
    assert "Telegram API timeout/network error" in warning_call
    assert "attempt 1/4" in warning_call
    
    info_call = mock_logger.info.call_args[0][0] 
    assert "Retrying in 1.0 seconds" in info_call

@pytest.mark.asyncio
async def test_retry_telegram_request_mixed_errors():
    """Test handling of mixed error types."""
    mock_operation = AsyncMock()
    mock_operation.side_effect = [
        NetworkError("network"),
        RetryAfter(2),
        TimedOut("timeout"),
        "success"
    ]
    
    with patch('src.utils.retry_utils.asyncio.sleep') as mock_sleep:
        result = await retry_telegram_request(mock_operation, max_retries=3)
    
    assert result == "success"
    assert mock_operation.call_count == 4
    
    # Check different delay patterns
    expected_delays = [1.0, 3.0, 4.0]  # exponential, retry_after+1, exponential
    actual_delays = [call.args[0] for call in mock_sleep.call_args_list]
    assert actual_delays == expected_delays

def test_get_retry_logger():
    """Test retry logger retrieval."""
    with patch('src.utils.retry_utils.get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        logger = get_retry_logger()
        
        assert logger == mock_logger
        mock_get_logger.assert_called_once()

@pytest.mark.asyncio
async def test_retry_telegram_request_zero_retries():
    """Test operation with zero retries."""
    mock_operation = AsyncMock()
    mock_operation.side_effect = TimedOut("timeout")
    
    with pytest.raises(TimedOut):
        await retry_telegram_request(mock_operation, max_retries=0)
    
    assert mock_operation.call_count == 1  # Only initial attempt

@pytest.mark.asyncio
async def test_retry_telegram_request_return_none():
    """Test that function returns None when no result from operation."""
    mock_operation = AsyncMock()
    mock_operation.side_effect = [TimedOut("timeout")] * 4  # More failures than retries
    
    with patch('src.utils.retry_utils.asyncio.sleep'):
        with pytest.raises(TimedOut):
            await retry_telegram_request(mock_operation, max_retries=2)
    
    # This test verifies the function doesn't return None incorrectly 