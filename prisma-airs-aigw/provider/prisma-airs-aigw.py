import logging
from collections.abc import Mapping

from dify_plugin import ModelProvider
from dify_plugin.errors.model import CredentialsValidateFailedError

logger = logging.getLogger(__name__)


class PrismaAirsAigwModelProvider(ModelProvider):
    def validate_provider_credentials(self, credentials: Mapping) -> None:
        """Validate provider credentials and persist them for model-level reuse."""
        try:
            from provider.utils import save_provider_credentials, validate_gateway

            creds = dict(credentials)
            validate_gateway(creds)
            save_provider_credentials(creds)
        except CredentialsValidateFailedError:
            raise
        except Exception as ex:
            logger.exception("prisma-airs-aigw credentials validation failed")
            raise CredentialsValidateFailedError(str(ex))
