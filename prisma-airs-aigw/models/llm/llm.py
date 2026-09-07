import logging
from collections.abc import Generator
from typing import Optional, Union

from dify_plugin import LargeLanguageModel
from dify_plugin.entities import I18nObject
from dify_plugin.entities.model import (
    AIModelEntity,
    DefaultParameterName,
    FetchFrom,
    ModelFeature,
    ModelType,
    ParameterRule,
    ParameterType,
)
from dify_plugin.entities.model.llm import LLMResult, LLMResultChunk, LLMResultChunkDelta
from dify_plugin.entities.model.message import (
    AssistantPromptMessage,
    DeveloperPromptMessage,
    ImagePromptMessageContent,
    PromptMessage,
    PromptMessageContentType,
    PromptMessageTool,
    SystemPromptMessage,
    TextPromptMessageContent,
    ToolPromptMessage,
    UserPromptMessage,
)
from dify_plugin.errors.model import (
    InvokeAuthorizationError,
    InvokeBadRequestError,
    InvokeConnectionError,
    InvokeError,
    InvokeRateLimitError,
    InvokeServerUnavailableError,
)

logger = logging.getLogger(__name__)

_THINKING_PREFIXES = ("o", "gpt-5")


def _uses_max_completion_tokens(model: str) -> bool:
    base = model.split(":", 2)[1] if model.startswith("ft:") else model
    return base.startswith(_THINKING_PREFIXES)


def _to_openai_messages(prompt_messages: list[PromptMessage]) -> list[dict]:
    result = []
    for msg in prompt_messages:
        if isinstance(msg, (SystemPromptMessage, DeveloperPromptMessage)):
            result.append({"role": msg.role.value, "content": _text_content(msg)})
        elif isinstance(msg, UserPromptMessage):
            if isinstance(msg.content, str):
                content = msg.content
            else:
                content = [_user_content_block(b) for b in (msg.content or [])]
            entry: dict = {"role": "user", "content": content}
            if msg.name:
                entry["name"] = msg.name
            result.append(entry)
        elif isinstance(msg, AssistantPromptMessage):
            entry = {"role": "assistant", "content": msg.content or ""}
            if msg.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ]
            if msg.name:
                entry["name"] = msg.name
            result.append(entry)
        elif isinstance(msg, ToolPromptMessage):
            result.append({
                "role": "tool",
                "content": _text_content(msg),
                "tool_call_id": msg.tool_call_id,
            })
        else:
            raise InvokeBadRequestError(f"Unsupported message type: {type(msg).__name__}")
    return result


def _text_content(msg: PromptMessage) -> str:
    if isinstance(msg.content, str):
        return msg.content
    parts = msg.content or []
    if any(p.type != PromptMessageContentType.TEXT for p in parts):
        raise InvokeBadRequestError(f"{msg.role.value} messages only support text content")
    return "".join(p.data for p in parts if isinstance(p, TextPromptMessageContent))


def _user_content_block(block) -> dict:
    if isinstance(block, TextPromptMessageContent):
        return {"type": "text", "text": block.data}
    if isinstance(block, ImagePromptMessageContent):
        return {"type": "image_url", "image_url": {"url": block.data}}
    raise InvokeBadRequestError(f"Unsupported content type: {block.type.value}")


def _to_openai_tools(tools: list[PromptMessageTool]) -> list[dict]:
    return [
        {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}}
        for t in tools
    ]


class PrismaAirsAigwLargeLanguageModel(LargeLanguageModel):

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        import openai

        return {
            InvokeAuthorizationError: [openai.AuthenticationError, openai.PermissionDeniedError],
            InvokeRateLimitError: [openai.RateLimitError],
            InvokeBadRequestError: [
                openai.BadRequestError,
                openai.UnprocessableEntityError,
                openai.NotFoundError,
            ],
            InvokeConnectionError: [openai.APIConnectionError, openai.APITimeoutError],
            InvokeServerUnavailableError: [openai.InternalServerError, openai.APIError],
        }

    def _invoke(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: Optional[list[PromptMessageTool]] = None,
        stop: Optional[list[str]] = None,
        stream: bool = True,
        user: Optional[str] = None,
    ) -> Union[LLMResult, Generator]:
        from provider.utils import get_client

        client = get_client(credentials)
        messages = _to_openai_messages(prompt_messages)

        params: dict = {"model": model, "messages": messages, "stream": stream}

        # Pass through all model_parameters; handle special cases explicitly.
        for k, v in model_parameters.items():
            if v is None or v == "":
                continue
            if k == "max_tokens":
                key = "max_completion_tokens" if _uses_max_completion_tokens(model) else "max_tokens"
                params[key] = v
            elif k == "response_format":
                params["response_format"] = {"type": v}
            else:
                params[k] = v

        if stop:
            params["stop"] = stop
        if tools:
            params["tools"] = _to_openai_tools(tools)
            params.setdefault("tool_choice", "auto")
        if user:
            params["user"] = user
        if stream:
            params["stream_options"] = {"include_usage": True}

        if stream:
            return self._stream_with_error_mapping(
                self._handle_stream(client, params, model, credentials, prompt_messages, tools)
            )
        return self._handle_non_stream(client, params, model, credentials, prompt_messages, tools)

    def _stream_with_error_mapping(self, generator: Generator) -> Generator:
        try:
            yield from generator
        except Exception as e:
            raise self._transform_invoke_error(e) from e

    def _call_with_stop_fallback(self, client, params: dict):
        """Retry without stop sequences if the backend doesn't support them."""
        import openai

        try:
            return client.chat.completions.create(**params)
        except openai.BadRequestError as e:
            msg = str(e).lower()
            if "stop" in params and any(kw in msg for kw in ("stopsequence", "stop_sequence", "stop sequences", "stopsequences")):
                return client.chat.completions.create(
                    **{k: v for k, v in params.items() if k != "stop"}
                )
            raise

    def _handle_non_stream(self, client, params, model, credentials, prompt_messages, tools):
        response = self._call_with_stop_fallback(client, params)
        choice = response.choices[0]
        reply = choice.message
        content = (reply.content or "") + (reply.refusal or "")

        raw_calls = [
            AssistantPromptMessage.ToolCall(
                id=tc.id or "",
                type="function",
                function=AssistantPromptMessage.ToolCall.ToolCallFunction(
                    name=tc.function.name or "",
                    arguments=tc.function.arguments or "",
                ),
            )
            for tc in (reply.tool_calls or [])
        ]
        calls = raw_calls if choice.finish_reason in ("tool_calls", "function_call") else []

        if response.usage:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
        else:
            prompt_tokens = self.get_num_tokens(model, credentials, prompt_messages, tools)
            completion_tokens = self.get_num_tokens(
                model, credentials,
                [AssistantPromptMessage(content=content, tool_calls=raw_calls)],
            )

        return LLMResult(
            model=response.model or model,
            prompt_messages=prompt_messages,
            message=AssistantPromptMessage(content=content, tool_calls=calls),
            usage=self._calc_response_usage(model, credentials, prompt_tokens, completion_tokens),
        )

    def _handle_stream(self, client, params, model, credentials, prompt_messages, tools) -> Generator:
        response = self._call_with_stop_fallback(client, params)
        text = ""
        usage = None
        finish_reason = None
        response_model = model
        fragments: dict[int, dict[str, str]] = {}

        try:
            for chunk in response:
                response_model = chunk.model or response_model
                if chunk.usage:
                    usage = chunk.usage
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                delta = choice.delta
                piece = (delta.content or "") + (delta.refusal or "")
                if piece:
                    text += piece
                    yield LLMResultChunk(
                        model=response_model,
                        delta=LLMResultChunkDelta(
                            index=choice.index,
                            message=AssistantPromptMessage(content=piece),
                        ),
                    )
                for part in delta.tool_calls or []:
                    frag = fragments.setdefault(part.index, {"id": "", "name": "", "arguments": ""})
                    frag["id"] = part.id or frag["id"]
                    if part.function:
                        frag["name"] = part.function.name or frag["name"]
                        frag["arguments"] += part.function.arguments or ""
                if choice.finish_reason:
                    finish_reason = choice.finish_reason
        finally:
            close = getattr(response, "close", None)
            if callable(close):
                close()

        if finish_reason is None:
            raise InvokeConnectionError("Stream ended without a finish reason")

        calls = (
            [
                AssistantPromptMessage.ToolCall(
                    id=item["id"],
                    type="function",
                    function=AssistantPromptMessage.ToolCall.ToolCallFunction(
                        name=item["name"], arguments=item["arguments"]
                    ),
                )
                for _, item in sorted(fragments.items())
            ]
            if finish_reason in ("tool_calls", "function_call")
            else []
        )

        if usage:
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
        else:
            prompt_tokens = self.get_num_tokens(model, credentials, prompt_messages, tools)
            completion_tokens = self.get_num_tokens(
                model, credentials,
                [AssistantPromptMessage(
                    content=text + "".join(v["arguments"] for v in sorted(fragments.values())),
                    tool_calls=calls,
                )],
            )

        yield LLMResultChunk(
            model=response_model,
            delta=LLMResultChunkDelta(
                index=0,
                message=AssistantPromptMessage(content="", tool_calls=calls),
                finish_reason="tool_calls" if calls else finish_reason,
                usage=self._calc_response_usage(model, credentials, prompt_tokens, completion_tokens),
            ),
        )

    def get_num_tokens(
        self,
        model: str,
        credentials: dict,
        prompt_messages: list[PromptMessage],
        tools: Optional[list[PromptMessageTool]] = None,
    ) -> int:
        try:
            import tiktoken
            try:
                enc = tiktoken.encoding_for_model(model)
            except KeyError:
                enc = tiktoken.get_encoding("cl100k_base")
            total = 0
            for msg in prompt_messages:
                total += 4
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                total += len(enc.encode(content))
            return total
        except Exception:
            return sum(
                len(msg.content if isinstance(msg.content, str) else str(msg.content)) // 4
                for msg in prompt_messages
            )

    def validate_credentials(self, model: str, credentials: dict) -> None:
        pass  # provider-level credentials are validated at provider setup; no per-model check needed

    def get_model_schema(self, model: str, credentials) -> AIModelEntity | None:
        return self.get_customizable_model_schema(model, credentials or {})

    def get_customizable_model_schema(self, model: str, credentials: dict) -> AIModelEntity:
        creds = credentials or {}
        try:
            context_size = int(creds.get("context_size", 32768))
        except (ValueError, TypeError):
            context_size = 32768

        features: list[ModelFeature] = []
        if creds.get("vision_support") == "support":
            features.append(ModelFeature.VISION)
        if creds.get("function_calling_type") == "tool_call":
            features.append(ModelFeature.MULTI_TOOL_CALL)
            features.append(ModelFeature.STREAM_TOOL_CALL)

        return AIModelEntity(
            model=model,
            label=I18nObject(zh_Hans=model, en_US=model),
            model_type=ModelType.LLM,
            features=features,
            fetch_from=FetchFrom.CUSTOMIZABLE_MODEL,
            model_properties={"mode": "chat", "context_size": context_size},
            parameter_rules=[
                ParameterRule(
                    name=DefaultParameterName.TEMPERATURE.value,
                    use_template=DefaultParameterName.TEMPERATURE.value,
                ),
                ParameterRule(
                    name=DefaultParameterName.TOP_P.value,
                    use_template=DefaultParameterName.TOP_P.value,
                ),
                ParameterRule(
                    name=DefaultParameterName.FREQUENCY_PENALTY.value,
                    use_template=DefaultParameterName.FREQUENCY_PENALTY.value,
                ),
                ParameterRule(
                    name=DefaultParameterName.PRESENCE_PENALTY.value,
                    use_template=DefaultParameterName.PRESENCE_PENALTY.value,
                ),
                ParameterRule(
                    name=DefaultParameterName.MAX_TOKENS.value,
                    use_template=DefaultParameterName.MAX_TOKENS.value,
                    required=True,
                    default=512,
                    min=1,
                    max=context_size,
                ),
                ParameterRule(
                    name=DefaultParameterName.RESPONSE_FORMAT.value,
                    use_template=DefaultParameterName.RESPONSE_FORMAT.value,
                ),
            ],
        )
