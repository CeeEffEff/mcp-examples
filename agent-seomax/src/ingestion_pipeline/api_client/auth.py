"""
GCP Authentication Module

Handles authentication with Google Cloud Platform using service accounts.
Provides credential management and authentication for all GCP API clients.
"""

import os
from typing import Optional, List
from pathlib import Path

from google.auth import default
from google.auth.credentials import Credentials
from google.oauth2 import service_account
import structlog

logger = structlog.get_logger(__name__)


class GCPAuthenticationError(Exception):
    """Raised when GCP authentication fails."""
    pass


class GCPAuthManager:
    """
    Manages GCP authentication using service accounts.
    
    Supports multiple authentication methods:
    1. Service account JSON key file
    2. Application Default Credentials (ADC)
    3. Environment-based credentials
    """
    
    def __init__(
        self,
        service_account_path: Optional[str] = None,
        scopes: Optional[List[str]] = None
    ):
        """
        Initialize the GCP authentication manager.
        
        Args:
            service_account_path: Path to service account JSON key file
            scopes: List of OAuth2 scopes required for API access
        """
        self.service_account_path = service_account_path
        self.scopes = scopes or self._get_default_scopes()
        self._credentials: Optional[Credentials] = None
        self._project_id: Optional[str] = None
        
        logger.info(
            "Initializing GCP authentication",
            service_account_path=service_account_path,
            scopes_count=len(self.scopes)
        )
    
    @staticmethod
    def _get_default_scopes() -> List[str]:
        """
        Get default OAuth2 scopes for GCP APIs.
        
        Returns:
            List of default OAuth2 scope URLs
        """
        return [
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/compute",
            "https://www.googleapis.com/auth/devstorage.read_write",
            "https://www.googleapis.com/auth/logging.admin",
            "https://www.googleapis.com/auth/monitoring",
            "https://www.googleapis.com/auth/pubsub",
            "https://www.googleapis.com/auth/sqlservice.admin",
        ]
    
    def authenticate(self) -> Credentials:
        """
        Authenticate with GCP and return credentials.
        
        Returns:
            Google Cloud credentials object
            
        Raises:
            GCPAuthenticationError: If authentication fails
        """
        if self._credentials:
            logger.debug("Using cached credentials")
            return self._credentials
        
        try:
            if self.service_account_path:
                self._credentials = self._authenticate_with_service_account()
            else:
                self._credentials = self._authenticate_with_default()
            
            logger.info(
                "GCP authentication successful",
                project_id=self._project_id,
                auth_method="service_account" if self.service_account_path else "default"
            )
            
            return self._credentials
            
        except Exception as e:
            logger.error(
                "GCP authentication failed",
                error=str(e),
                service_account_path=self.service_account_path
            )
            raise GCPAuthenticationError(f"Failed to authenticate with GCP: {str(e)}")
    
    def _authenticate_with_service_account(self) -> Credentials:
        """
        Authenticate using service account JSON key file.
        
        Returns:
            Service account credentials
            
        Raises:
            GCPAuthenticationError: If service account file is invalid
        """
        if not self.service_account_path:
            raise GCPAuthenticationError("Service account path not provided")
        
        key_path = Path(self.service_account_path)
        
        if not key_path.exists():
            raise GCPAuthenticationError(
                f"Service account key file not found: {self.service_account_path}"
            )
        
        logger.debug(
            "Authenticating with service account",
            key_path=str(key_path)
        )
        
        credentials = service_account.Credentials.from_service_account_file(
            str(key_path),
            scopes=self.scopes
        )
        
        # Extract project ID from service account
        with open(key_path, 'r') as f:
            import json
            key_data = json.load(f)
            self._project_id = key_data.get('project_id')
        
        return credentials
    
    def _authenticate_with_default(self) -> Credentials:
        """
        Authenticate using Application Default Credentials (ADC).
        
        Returns:
            Default credentials
            
        Raises:
            GCPAuthenticationError: If default credentials are not available
        """
        logger.debug("Authenticating with Application Default Credentials")
        
        credentials, project_id = default(scopes=self.scopes)
        self._project_id = project_id
        
        if not credentials:
            raise GCPAuthenticationError(
                "Could not obtain default credentials. "
                "Ensure GOOGLE_APPLICATION_CREDENTIALS is set or gcloud is configured."
            )
        
        return credentials
    
    def get_project_id(self) -> str:
        """
        Get the GCP project ID associated with credentials.
        
        Returns:
            GCP project ID
            
        Raises:
            GCPAuthenticationError: If project ID cannot be determined
        """
        if not self._project_id:
            # Try to get from environment
            self._project_id = os.getenv('GCP_PROJECT_ID') or os.getenv('GOOGLE_CLOUD_PROJECT')
            
            if not self._project_id:
                # Try to authenticate to get project ID
                self.authenticate()
            
            if not self._project_id:
                raise GCPAuthenticationError(
                    "Could not determine GCP project ID. "
                    "Set GCP_PROJECT_ID or GOOGLE_CLOUD_PROJECT environment variable."
                )
        
        return self._project_id
    
    def refresh_credentials(self) -> Credentials:
        """
        Force refresh of credentials.
        
        Returns:
            Refreshed credentials
        """
        logger.info("Refreshing GCP credentials")
        self._credentials = None
        return self.authenticate()
    
    def validate_credentials(self) -> bool:
        """
        Validate that credentials are working.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            credentials = self.authenticate()
            
            # Try to refresh the credentials to validate
            if hasattr(credentials, 'refresh'):
                from google.auth.transport import requests
                credentials.refresh(requests.Request())
            
            logger.info("Credentials validated successfully")
            return True
            
        except Exception as e:
            logger.error("Credential validation failed", error=str(e))
            return False
