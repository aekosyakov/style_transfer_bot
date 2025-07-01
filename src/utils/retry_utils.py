"""Retry utilities for Telegram API calls."""

import asyncio
from telegram.error import TimedOut, NetworkError, RetryAfter
from .logging_utils import get_logger

def get_retry_logger():
    """Get logger instance for retry operations."""
    return get_logger()

async def retry_telegram_request(operation, max_retries=3, initial_delay=1.0):
    """
    Retry Telegram API requests with exponential backoff for timeout and network errors.
    
    Args:
        operation: Async function to retry
        max_retries: Maximum number of retry attempts  
        initial_delay: Initial delay between retries (seconds)
    
    Returns:
        Result of the operation or None if all retries failed
        
    Raises:
        TimedOut: If all retries failed due to timeouts
        NetworkError: If all retries failed due to network errors
        RetryAfter: If rate limit exceeded after all retries
        Exception: For non-retryable errors
    """
    logger = get_retry_logger()
    
    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except (TimedOut, NetworkError) as e:
            if attempt < max_retries:
                delay = initial_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Telegram API timeout/network error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                logger.info(f"Retrying in {delay:.1f} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {max_retries + 1} attempts failed for Telegram API call: {e}")
                raise e
        except RetryAfter as e:
            if attempt < max_retries:
                delay = e.retry_after + 1  # Add 1 second buffer
                logger.warning(f"Telegram rate limit hit (attempt {attempt + 1}/{max_retries + 1}): retry after {e.retry_after}s")
                logger.info(f"Waiting {delay} seconds before retry...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Rate limit exceeded after {max_retries + 1} attempts: {e}")
                raise e
        except Exception as e:
            # Don't retry for other types of errors
            logger.error(f"Non-retryable error in Telegram API call: {type(e).__name__}: {e}")
            raise e
    
    return None 