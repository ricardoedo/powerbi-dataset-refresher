"""Authentication service for Azure AD and Power BI API."""

import logging
from datetime import datetime, timedelta
from typing import Optional
import requests

from .exceptions import AuthenticationError
from .retry import RetryHandler


logger = logging.getLogger(__name__)


class AuthenticationService:
    """Service for authenticating with Azure AD and managing access tokens."""

    def __init__(self, tenant_id: str, client_id: str, client_secret: str,
                 retry_handler: Optional[RetryHandler] = None):
        """
        Initialize authentication service with service principal credentials.

        Args:
            tenant_id: Azure AD tenant ID
            client_id: Service principal client ID (application ID)
            client_secret: Service principal client secret
            retry_handler: Optional retry handler for network errors.
                         If None, creates a default handler.
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.retry_handler = retry_handler or RetryHandler()

        # Token cache
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

        # Azure AD and Power BI constants
        self._authority_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        self._scope = "https://analysis.windows.net/powerbi/api/.default"

    def get_access_token(self) -> str:
        """
        Get a valid access token for Power BI API.

        Returns cached token if still valid, otherwise requests a new token.
        Automatically renews expired tokens.

        Returns:
            Valid JWT access token

        Raises:
            AuthenticationError: If authentication fails after retries
        """
        # Check if we have a valid cached token
        if self.is_token_valid():
            logger.debug("Using cached access token")
            return self._access_token

        logger.info("Requesting new access token from Azure AD")

        try:
            # Use retry handler for network resilience
            token_response = self.retry_handler.execute_with_retry(
                self._request_token
            )

            # Cache the token and expiry time
            self._access_token = token_response['access_token']
            expires_in = token_response.get('expires_in', 3600)

            # Set expiry with 5-minute buffer to avoid edge cases
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)

            logger.info("Successfully obtained access token (expires in %d seconds)", expires_in)
            return self._access_token

        except Exception as e:
            logger.error("Failed to obtain access token: %s", str(e))
            raise AuthenticationError(f"Authentication failed: {str(e)}") from e

    def is_token_valid(self) -> bool:
        """
        Check if the current cached token is valid.

        A token is considered valid if:
        1. It exists in the cache
        2. Its expiry time has not been reached

        Returns:
            True if token is valid, False otherwise
        """
        if self._access_token is None or self._token_expiry is None:
            return False

        # Check if token has expired
        return datetime.now() < self._token_expiry

    def _request_token(self) -> dict:
        """
        Request a new access token from Azure AD.

        This is the internal method that makes the actual HTTP request.
        It's separated to allow the retry handler to wrap it.

        Returns:
            Token response dictionary with 'access_token' and 'expires_in'

        Raises:
            AuthenticationError: If the request fails
        """
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self._scope
        }

        try:
            response = requests.post(
                self._authority_url,
                data=payload,
                timeout=30
            )

            # Check for authentication errors
            if response.status_code == 401:
                error_msg = "Invalid credentials: Check tenant_id, client_id, and client_secret"
                logger.error(error_msg)
                raise AuthenticationError(error_msg)

            if response.status_code == 403:
                error_msg = "Forbidden: Service principal may lack required permissions"
                logger.error(error_msg)
                raise AuthenticationError(error_msg)

            # Check for other HTTP errors
            if not response.ok:
                error_msg = f"Authentication request failed with status {response.status_code}"
                logger.error("%s: %s", error_msg, response.text)
                raise AuthenticationError(f"{error_msg}: {response.text}")

            # Parse and validate response
            token_data = response.json()

            if 'access_token' not in token_data:
                error_msg = "Invalid token response: missing access_token"
                logger.error(error_msg)
                raise AuthenticationError(error_msg)

            return token_data

        except requests.exceptions.Timeout as e:
            error_msg = "Authentication request timed out"
            logger.error(error_msg)
            raise AuthenticationError(error_msg) from e

        except requests.exceptions.ConnectionError as e:
            error_msg = "Failed to connect to Azure AD"
            logger.error(error_msg)
            raise AuthenticationError(error_msg) from e

        except requests.exceptions.RequestException as e:
            error_msg = f"Authentication request failed: {str(e)}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg) from e

        except ValueError as e:
            # JSON parsing error
            error_msg = f"Invalid JSON response from Azure AD: {str(e)}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg) from e
