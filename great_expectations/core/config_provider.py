from __future__ import annotations

import errno
import os
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Any, Dict, Optional, Type, cast

from great_expectations.core.config_substitutor import ConfigurationSubstitutor
from great_expectations.core.yaml_handler import YAMLHandler
from great_expectations.data_context.types.base import GXCloudConfig

yaml = YAMLHandler()


class AbstractConfigurationProvider(ABC):
    def __init__(self) -> None:
        self._substitutor = ConfigurationSubstitutor()

    @abstractmethod
    def get_values(self) -> Dict[str, str]:
        """
        Retrieve any configuration variables relevant to the provider's environment.
        """
        pass

    def substitute_config(
        self, config: Any, config_values: Optional[Dict[str, str]] = None
    ) -> Any:
        """
        Utilizes the underlying ConfigurationSubstitutor instance to substitute any
        $VARIABLES with their corresponding config variable value.

        Args:
            config: The config object to update.
            config_values: The dictionary of values to use during the substitution process.
                           If omitted, any values derived from registered providers will be used.

        Returns:
            The input config object with any $VARIABLES replaced with their corresponding config values.
        """
        if config_values is None:
            config_values = self.get_values()
        return self._substitutor.substitute_all_config_variables(config, config_values)


class ConfigurationProvider(AbstractConfigurationProvider):
    """
    Wrapper class around the other environment-specific configuraiton provider classes.

    Based on relevance, specific providers are registered to this object and are invoked
    using the API defined by the AbstractConfigurationProvider.

    In short, this class' purpose is to aggregate all configuration variables that may
    be present for a given user environment (config variables, env vars, runtime environment, etc.)
    """

    def __init__(self) -> None:
        self._providers: OrderedDict[
            Type[AbstractConfigurationProvider], AbstractConfigurationProvider
        ] = OrderedDict()
        super().__init__()

    def register_provider(self, provider: AbstractConfigurationProvider) -> None:
        """
        Saves a configuration provider to the object's state for downstream usage.
        See `get_values()` for more information.

        Args:
            provider: An instance of a provider to register.
        """
        type_ = type(provider)
        if type_ in self._providers:
            raise ValueError(f"Provider of type {type_} has already been registered!")
        self._providers[type_] = provider

    def get_provider(
        self, type_: Type[AbstractConfigurationProvider]
    ) -> Optional[AbstractConfigurationProvider]:
        """
        Retrieves a registered configuration provider (if available).

        Args:
            type_: The class of the configuration provider to retrieve.

        Returns:
            A registered provider if available.
            If not, None is returned.
        """
        return self._providers.get(type_)

    def get_values(self) -> Dict[str, str]:
        """
        Iterates through all registered providers to aggregate a list of configuration values.

        Values are generated based on the order of registration; if there is a conflict,
        subsequent providers will overwrite existing values.
        """
        values: Dict[str, str] = {}
        for provider in self._providers.values():
            values.update(provider.get_values())
        return values


class RuntimeEnvironmentConfigurationProvider(AbstractConfigurationProvider):
    """
    Responsible for the management of the runtime_environment dictionary provided at runtime.
    """

    def __init__(self, runtime_environment: Dict[str, str]) -> None:
        self._runtime_environment = runtime_environment
        super().__init__()

    def get_values(self) -> Dict[str, str]:
        return self._runtime_environment


class EnvironmentConfigurationProvider(AbstractConfigurationProvider):
    """
    Responsible for the management of environment variables.
    """

    def __init__(self) -> None:
        super().__init__()

    def get_values(self) -> Dict[str, str]:
        return dict(os.environ)


class ConfigurationVariablesConfigurationProvider(AbstractConfigurationProvider):
    """
    Responsible for the management of user-defined configuration variables.

    These can be found in the user's /uncommitted/config_variables.yml file.
    """

    def __init__(
        self, config_variables_file_path: str, root_directory: Optional[str] = None
    ) -> None:
        self._config_variables_file_path = config_variables_file_path
        self._root_directory = root_directory
        super().__init__()

    def get_values(self) -> Dict[str, str]:
        env_vars = dict(os.environ)
        try:
            # If the user specifies the config variable path with an environment variable, we want to substitute it
            defined_path: str = self._substitutor.substitute_config_variable(  # type: ignore[assignment]
                self._config_variables_file_path, env_vars
            )
            if not os.path.isabs(defined_path):
                root_directory: str = self._root_directory or os.curdir
            else:
                root_directory = ""

            var_path = os.path.join(root_directory, defined_path)
            with open(var_path) as config_variables_file:
                contents = config_variables_file.read()

            variables = dict(yaml.load(contents)) or {}
            return cast(
                Dict[str, str],
                self._substitutor.substitute_all_config_variables(variables, env_vars),
            )

        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
            return {}


class CloudConfigurationProvider(AbstractConfigurationProvider):
    """
    Responsible for the management of a user's GX Cloud credentials.

    See `GeCloudConfig` for more information. Note that this is only registered on the primary
    config provider when in a Cloud-backend environment.
    """

    def __init__(self, cloud_config: GXCloudConfig) -> None:
        self._cloud_config = cloud_config

    def get_values(self) -> Dict[str, str]:
        from great_expectations.data_context.cloud_constants import (
            GXCloudEnvironmentVariable,
        )

        return {
            GXCloudEnvironmentVariable.BASE_URL: self._cloud_config.base_url,
            GXCloudEnvironmentVariable.ACCESS_TOKEN: self._cloud_config.access_token,
            GXCloudEnvironmentVariable.ORGANIZATION_ID: self._cloud_config.organization_id,  # type: ignore[dict-item]
        }