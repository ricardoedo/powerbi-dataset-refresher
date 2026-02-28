"""Retry handler with exponential backoff for Power BI operations."""

import time
import logging
from typing import Callable, Any, List
from requests.exceptions import ConnectionError as RequestsConnectionError, Timeout, RequestException

from .exceptions import PowerBIAPIError, AuthenticationError, PowerBIPermissionError


logger = logging.getLogger(__name__)


class RetryHandler:
    """Handles retries with exponential backoff for transient errors."""
    
    def __init__(self, max_retries: int = 3, backoff_delays: List[int] = None):
        """
        Initialize retry handler with configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            backoff_delays: List of delays in seconds for each retry attempt.
                          Defaults to [5, 10, 20] for exponential backoff.
        """
        self.max_retries = max_retries
        self.backoff_delays = backoff_delays or [5, 10, 20]
        
        # Ensure we have enough delays for max_retries
        if len(self.backoff_delays) < max_retries:
            # Extend with exponential pattern
            last_delay = self.backoff_delays[-1] if self.backoff_delays else 5
            while len(self.backoff_delays) < max_retries:
                last_delay *= 2
                self.backoff_delays.append(last_delay)
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with automatic retries for transient errors.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function
            
        Raises:
            Exception: If all retry attempts fail, raises the last exception
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # +1 for initial attempt
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Check if this is the last attempt
                if attempt >= self.max_retries:
                    logger.error(
                        "All %d retry attempts exhausted. Final error: %s",
                        self.max_retries,
                        str(e)
                    )
                    raise
                
                # Check if we should retry this exception
                if not self.should_retry(e):
                    logger.error("Non-retryable error encountered: %s", str(e))
                    raise
                
                # Calculate delay for this attempt
                delay = self.backoff_delays[attempt]
                
                logger.warning(
                    "Attempt %d/%d failed: %s. Retrying in %d seconds...",
                    attempt + 1,
                    self.max_retries,
                    str(e),
                    delay
                )
                
                time.sleep(delay)
        
        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
    
    def should_retry(self, exception: Exception) -> bool:
        """
        Determine if an exception is retryable.
        
        Retryable errors include:
        - Network errors (ConnectionError, Timeout)
        - HTTP 5xx server errors
        - Transient request exceptions
        
        Non-retryable errors include:
        - Authentication errors (401, 403)
        - Permission errors
        - Client errors (4xx except 429)
        
        Args:
            exception: The exception to evaluate
            
        Returns:
            True if the error should be retried, False otherwise
        """
        # Network and timeout errors are always retryable
        if isinstance(exception, (RequestsConnectionError, Timeout)):
            return True
        
        # Generic request exceptions are retryable
        if isinstance(exception, RequestException):
            return True
        
        # Authentication and permission errors are not retryable
        if isinstance(exception, (AuthenticationError, PowerBIPermissionError)):
            return False
        
        # Check PowerBIAPIError status codes
        if isinstance(exception, PowerBIAPIError):
            status_code = exception.status_code
            
            # 5xx server errors are retryable
            if 500 <= status_code < 600:
                return True
            
            # 429 rate limit is handled separately, not through normal retry
            if status_code == 429:
                return False
            
            # 4xx client errors are not retryable (except 429 handled above)
            if 400 <= status_code < 500:
                return False
        
        # By default, don't retry unknown exceptions
        return False
    
    def handle_rate_limit(self, retry_after: int = None):
        """
        Handle HTTP 429 rate limit responses.
        
        Waits for the time specified in the Retry-After header,
        or a default of 60 seconds if not specified.
        
        Args:
            retry_after: Number of seconds to wait (from Retry-After header).
                        If None, defaults to 60 seconds.
        """
        wait_time = retry_after if retry_after is not None else 60
        
        logger.warning(
            "Rate limit (429) encountered. Waiting %d seconds before retrying...",
            wait_time
        )
        
        time.sleep(wait_time)
