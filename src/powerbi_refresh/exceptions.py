"""Custom exceptions for Power BI refresh script."""


class PowerBIScriptError(Exception):
    """Base exception for all Power BI script errors."""


class AuthenticationError(PowerBIScriptError):
    """Error during authentication with Azure AD."""


class PowerBIAPIError(PowerBIScriptError):
    """Error when interacting with Power BI API."""
    
    def __init__(self, message: str, status_code: int, response_body: str):
        """
        Initialize API error with details.
        
        Args:
            message: Error message
            status_code: HTTP status code
            response_body: Response body from API
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class ConfigurationError(PowerBIScriptError):
    """Error in script configuration."""


class PowerBIPermissionError(PowerBIScriptError):
    """Error due to insufficient permissions on workspace or dataset."""


class RefreshTimeoutError(PowerBIScriptError):
    """Error when refresh exceeds maximum wait time."""
