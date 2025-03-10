# ---------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# ---------------------------------------------------------
import os
from abc import ABC, abstractmethod
from typing import List

from promptflow._constants import ConnectionProviderConfig
from promptflow.core._connection import _Connection
from promptflow.core._connection_provider._utils import extract_workspace
from promptflow.core._errors import MissingRequiredPackage, UnsupportedConnectionProviderConfig


class ConnectionProvider(ABC):
    """The connection provider interface to list/get connections in the current environment."""

    PROVIDER_CONFIG_KEY = "CONNECTION_PROVIDER_CONFIG"
    _instance = None

    @abstractmethod
    def get(self, name: str, **kwargs) -> _Connection:
        """Get connection by name."""
        raise NotImplementedError("Method 'get' is not implemented.")

    @abstractmethod
    def list(self, **kwargs) -> List[_Connection]:
        """List all connections without secrets."""
        raise NotImplementedError("Method 'list' is not implemented.")

    @classmethod
    def get_instance(cls) -> "ConnectionProvider":
        """Get the connection provider instance in the current environment.
        It will returned different implementations based on the current environment.
        """
        if not cls._instance:
            cls._instance = cls._init_from_env()
        return cls._instance

    @classmethod
    def init_from_provider_config(cls, provider_config: str, credential=None):
        """Initialize the connection provider from a provider config.

        Expected value:
        - local
        - azureml://subscriptions/<your-subscription>/resourceGroups/<your-resourcegroup>/
        providers/Microsoft.MachineLearningServices/workspaces/<your-workspace>
        """
        if not provider_config or provider_config == ConnectionProviderConfig.LOCAL:
            try:
                from promptflow._sdk._connection_provider._local_connection_provider import LocalConnectionProvider
            except ImportError as e:
                raise MissingRequiredPackage(message="Please install 'promptflow' to use local connection.") from e
            return LocalConnectionProvider()
        if provider_config.startswith(ConnectionProviderConfig.AZUREML):
            from promptflow.core._connection_provider._workspace_connection_provider import WorkspaceConnectionProvider

            subscription_id, resource_group, workspace_name = extract_workspace(provider_config)
            return WorkspaceConnectionProvider(subscription_id, resource_group, workspace_name, credential)
        raise UnsupportedConnectionProviderConfig(
            message=f"Unsupported connection provider config: {provider_config}, only 'local' and "
            "'azureml://subscriptions/<your-subscription>/resourceGroups/<your-resourcegroup>/"
            "providers/Microsoft.MachineLearningServices/workspaces/<your-workspace>' are expected as value."
        )

    @classmethod
    def _init_from_env(cls) -> "ConnectionProvider":
        """Initialize the connection provider from environment variables."""
        from ._http_connection_provider import HttpConnectionProvider

        endpoint = os.getenv(HttpConnectionProvider.ENDPOINT_KEY)
        if endpoint:
            return HttpConnectionProvider(endpoint)
        provider_config = os.getenv(cls.PROVIDER_CONFIG_KEY, "")
        return ConnectionProvider.init_from_provider_config(provider_config)
