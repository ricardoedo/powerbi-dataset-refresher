"""Configuration management for Power BI refresh script."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .exceptions import ConfigurationError


@dataclass
class Config:
    """Configuration for the Power BI refresh script."""
    
    tenant_id: str
    client_id: str
    client_secret: str
    workspace_ids: List[str]
    dataset_ids: Optional[List[str]] = None
    poll_interval: int = 30
    max_retries: int = 3
    retry_backoff: List[int] = field(default_factory=lambda: [5, 10, 20])
    log_level: str = "INFO"
    log_file: Optional[str] = None
    timeout: int = 3600


class ConfigManager:
    """Manages loading and validation of configuration."""
    
    @staticmethod
    def load(config_path: Optional[str] = None, 
             cli_args: Optional[Dict] = None) -> Config:
        """
        Load configuration from file and environment variables.
        
        Precedence order (highest to lowest):
        1. CLI arguments
        2. Configuration file
        3. Environment variables
        
        Args:
            config_path: Path to configuration file (JSON or YAML)
            cli_args: Dictionary of CLI arguments
            
        Returns:
            Config object with merged configuration
            
        Raises:
            ConfigurationError: If configuration cannot be loaded or is invalid
        """
        config_dict = {}
        
        # Layer 1: Environment variables (lowest precedence)
        config_dict.update(ConfigManager._load_from_env())
        
        # Layer 2: Configuration file
        if config_path:
            config_dict.update(ConfigManager._load_from_file(config_path))
        
        # Layer 3: CLI arguments (highest precedence)
        if cli_args:
            config_dict.update(ConfigManager._filter_cli_args(cli_args))
        
        # Create Config object
        try:
            config = Config(**config_dict)
        except TypeError as e:
            raise ConfigurationError(f"Invalid configuration: {e}") from e
        
        # Validate configuration
        errors = ConfigManager.validate(config)
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
            raise ConfigurationError(error_msg)
        
        return config
    
    @staticmethod
    def _load_from_env() -> Dict:
        """Load configuration from environment variables."""
        config = {}
        
        # Required fields
        if tenant_id := os.getenv("AZURE_TENANT_ID"):
            config["tenant_id"] = tenant_id
        if client_id := os.getenv("AZURE_CLIENT_ID"):
            config["client_id"] = client_id
        if client_secret := os.getenv("AZURE_CLIENT_SECRET"):
            config["client_secret"] = client_secret
        
        # Workspace IDs (comma-separated)
        if workspace_ids := os.getenv("POWERBI_WORKSPACE_IDS"):
            config["workspace_ids"] = [wid.strip() for wid in workspace_ids.split(",")]
        
        # Dataset IDs (comma-separated, optional)
        if dataset_ids := os.getenv("POWERBI_DATASET_IDS"):
            config["dataset_ids"] = [did.strip() for did in dataset_ids.split(",")]
        
        # Optional fields with defaults
        if poll_interval := os.getenv("POLL_INTERVAL"):
            try:
                config["poll_interval"] = int(poll_interval)
            except ValueError as exc:
                raise ConfigurationError("Invalid POLL_INTERVAL: must be an integer") from exc
        
        if max_retries := os.getenv("MAX_RETRIES"):
            try:
                config["max_retries"] = int(max_retries)
            except ValueError as exc:
                raise ConfigurationError("Invalid MAX_RETRIES: must be an integer") from exc
        
        if retry_backoff := os.getenv("RETRY_BACKOFF"):
            try:
                config["retry_backoff"] = [int(x.strip()) for x in retry_backoff.split(",")]
            except ValueError as exc:
                raise ConfigurationError("Invalid RETRY_BACKOFF: must be comma-separated integers") from exc
        
        if log_level := os.getenv("LOG_LEVEL"):
            config["log_level"] = log_level
        
        if log_file := os.getenv("LOG_FILE"):
            config["log_file"] = log_file
        
        if timeout := os.getenv("TIMEOUT"):
            try:
                config["timeout"] = int(timeout)
            except ValueError as exc:
                raise ConfigurationError("Invalid TIMEOUT: must be an integer") from exc
        
        return config

    @staticmethod
    def _load_from_file(config_path: str) -> Dict:
        """
        Load configuration from JSON or YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dictionary with configuration values
            
        Raises:
            ConfigurationError: If file cannot be read or parsed
        """
        path = Path(config_path)
        
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix in ['.json']:
                    data = json.load(f)
                elif path.suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                else:
                    raise ConfigurationError(
                        f"Unsupported configuration file format: {path.suffix}. "
                        "Supported formats: .json, .yaml, .yml"
                    )
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}") from e
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Error reading configuration file: {e}") from e
        
        # Flatten nested structure if present
        config = {}
        
        # Handle nested azure section
        if "azure" in data:
            azure = data["azure"]
            if "tenant_id" in azure:
                config["tenant_id"] = azure["tenant_id"]
            if "client_id" in azure:
                config["client_id"] = azure["client_id"]
            if "client_secret" in azure:
                config["client_secret"] = azure["client_secret"]
        
        # Handle nested powerbi section
        if "powerbi" in data:
            powerbi = data["powerbi"]
            if "workspaces" in powerbi:
                # Extract workspace IDs from workspace objects
                workspaces = powerbi["workspaces"]
                workspace_ids = []
                dataset_ids = []
                
                for ws in workspaces:
                    if isinstance(ws, dict):
                        if "id" in ws:
                            workspace_ids.append(ws["id"])
                        if "datasets" in ws and ws["datasets"]:
                            dataset_ids.extend(ws["datasets"])
                    else:
                        workspace_ids.append(ws)
                
                if workspace_ids:
                    config["workspace_ids"] = workspace_ids
                if dataset_ids:
                    config["dataset_ids"] = dataset_ids
        
        # Handle nested execution section
        if "execution" in data:
            execution = data["execution"]
            if "poll_interval" in execution:
                config["poll_interval"] = execution["poll_interval"]
            if "timeout" in execution:
                config["timeout"] = execution["timeout"]
            if "max_retries" in execution:
                config["max_retries"] = execution["max_retries"]
            if "retry_backoff" in execution:
                config["retry_backoff"] = execution["retry_backoff"]
        
        # Handle nested logging section
        if "logging" in data:
            logging = data["logging"]
            if "level" in logging:
                config["log_level"] = logging["level"]
            if "file" in logging:
                config["log_file"] = logging["file"]
        
        # Handle flat structure (direct keys)
        for key in ["tenant_id", "client_id", "client_secret", "workspace_ids", 
                    "dataset_ids", "poll_interval", "timeout", "max_retries", 
                    "retry_backoff", "log_level", "log_file"]:
            if key in data and key not in config:
                config[key] = data[key]
        
        return config
    
    @staticmethod
    def _filter_cli_args(cli_args: Dict) -> Dict:
        """
        Filter and transform CLI arguments to config format.
        
        Args:
            cli_args: Dictionary of CLI arguments
            
        Returns:
            Dictionary with filtered configuration values
        """
        config = {}
        
        # Map CLI argument names to config field names
        arg_mapping = {
            "config": None,  # Skip, already processed
            "workspace_id": "workspace_ids",
            "dataset_id": "dataset_ids",
            "log_level": "log_level",
            "log_file": "log_file",
            "poll_interval": "poll_interval",
            "timeout": "timeout",
            "max_retries": "max_retries",
            "tenant_id": "tenant_id",
            "client_id": "client_id",
            "client_secret": "client_secret",
        }
        
        for cli_key, config_key in arg_mapping.items():
            if config_key and cli_key in cli_args and cli_args[cli_key] is not None:
                value = cli_args[cli_key]
                
                # Handle list arguments (workspace_ids, dataset_ids)
                if config_key in ["workspace_ids", "dataset_ids"]:
                    if isinstance(value, list):
                        config[config_key] = value
                    else:
                        config[config_key] = [value]
                else:
                    config[config_key] = value
        
        return config
    
    @staticmethod
    def validate(config: Config) -> List[str]:
        """
        Validate configuration and return list of errors.
        
        Args:
            config: Config object to validate
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Required fields
        if not config.tenant_id:
            errors.append("Missing required field: tenant_id")
        if not config.client_id:
            errors.append("Missing required field: client_id")
        if not config.client_secret:
            errors.append("Missing required field: client_secret")
        if not config.workspace_ids:
            errors.append("Missing required field: workspace_ids (at least one workspace required)")
        
        # Validate GUID format for IDs
        import re
        guid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        
        if config.tenant_id and not guid_pattern.match(config.tenant_id):
            errors.append("Invalid tenant_id format: must be a valid GUID")
        
        if config.client_id and not guid_pattern.match(config.client_id):
            errors.append("Invalid client_id format: must be a valid GUID")
        
        if config.workspace_ids:
            for wid in config.workspace_ids:
                if not guid_pattern.match(wid):
                    errors.append(f"Invalid workspace_id format: {wid} (must be a valid GUID)")
        
        if config.dataset_ids:
            for did in config.dataset_ids:
                if not guid_pattern.match(did):
                    errors.append(f"Invalid dataset_id format: {did} (must be a valid GUID)")
        
        # Validate numeric ranges
        if config.poll_interval <= 0:
            errors.append(f"Invalid poll_interval: {config.poll_interval} (must be > 0)")
        
        if config.max_retries < 0:
            errors.append(f"Invalid max_retries: {config.max_retries} (must be >= 0)")
        
        if config.timeout <= 0:
            errors.append(f"Invalid timeout: {config.timeout} (must be > 0)")
        
        # Validate retry_backoff
        if not config.retry_backoff:
            errors.append("Invalid retry_backoff: must contain at least one value")
        elif any(delay <= 0 for delay in config.retry_backoff):
            errors.append("Invalid retry_backoff: all delays must be > 0")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if config.log_level.upper() not in valid_log_levels:
            errors.append(
                f"Invalid log_level: {config.log_level} "
                f"(must be one of {', '.join(valid_log_levels)})"
            )
        
        return errors
