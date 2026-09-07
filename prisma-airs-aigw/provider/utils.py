import json
import os

_PROVIDER_CREDS_FILE = os.path.join(os.path.dirname(__file__), ".provider_creds.json")
_PROVIDER_CRED_KEYS = ("api_base_url", "api_key", "api_key_header", "tls_verify")


def save_provider_credentials(credentials: dict) -> None:
    subset = {k: credentials[k] for k in _PROVIDER_CRED_KEYS if k in credentials}
    with open(_PROVIDER_CREDS_FILE, "w", encoding="utf-8") as f:
        json.dump(subset, f)


def load_provider_credentials() -> dict:
    try:
        with open(_PROVIDER_CREDS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def resolve_credentials(credentials: dict) -> dict:
    """Merge model-level credentials with saved provider credentials.

    Provider-level values are the base; any non-empty model-level value overrides.
    This lets models share the provider's api_base_url and api_key without requiring
    users to re-enter them per model.
    """
    merged = dict(load_provider_credentials())
    for k in _PROVIDER_CRED_KEYS:
        v = credentials.get(k)
        if v:
            merged[k] = v
    merged.setdefault("api_base_url", "https://aigw.portkey.ai/v1")
    merged.setdefault("api_key_header", "x-portkey-api-key")
    merged.setdefault("tls_verify", "true")
    return merged


def _make_http_client(creds: dict):
    import httpx

    tls_verify = creds.get("tls_verify", "true") == "true"
    api_key = creds["api_key"]
    header_name = creds.get("api_key_header", "x-portkey-api-key").strip()

    def _inject_auth(request: httpx.Request) -> None:
        if "authorization" in request.headers:
            del request.headers["authorization"]
        request.headers[header_name] = api_key

    return httpx.Client(verify=tls_verify, event_hooks={"request": [_inject_auth]})


def get_client(credentials: dict):
    from openai import OpenAI

    creds = resolve_credentials(credentials)
    return OpenAI(
        api_key="placeholder",
        base_url=creds.get("api_base_url", "https://aigw.portkey.ai/v1"),
        http_client=_make_http_client(creds),
    )


def validate_gateway(credentials: dict) -> None:
    """Verify credentials by making a minimal chat completion call."""
    import openai
    from dify_plugin.errors.model import CredentialsValidateFailedError

    creds = resolve_credentials(credentials)
    if not creds.get("api_key"):
        raise CredentialsValidateFailedError("API Key is required")

    validation_model = credentials.get("validation_model", "").strip()
    if not validation_model:
        raise CredentialsValidateFailedError("Validation model name is required")

    client = openai.OpenAI(
        api_key="placeholder",
        base_url=creds.get("api_base_url", "https://aigw.portkey.ai/v1"),
        http_client=_make_http_client(creds),
    )

    try:
        client.chat.completions.create(
            model=validation_model,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
            stream=False,
        )
    except CredentialsValidateFailedError:
        raise
    except openai.AuthenticationError:
        raise CredentialsValidateFailedError("Authentication failed. Check your API key.")
    except openai.NotFoundError:
        raise CredentialsValidateFailedError(
            f"Model '{validation_model}' not found on gateway. Check the validation model name."
        )
    except openai.APIConnectionError as e:
        raise CredentialsValidateFailedError(f"Cannot reach gateway: {e}")
    except Exception as e:
        raise CredentialsValidateFailedError(f"Validation failed: {e}")
