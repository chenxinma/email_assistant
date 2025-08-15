import os
import os
from typing import Literal, Optional, Union

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from typing_extensions import TypeAliasType

api_key = os.environ.get("BAILIAN_API_KEY", "")

KnownModelName = TypeAliasType(
    'KnownModelName',
    Literal[
        "qwen-plus",
        "qwen-turbo",
        "qwen-max",
        "qwen3-coder-plus"
    ]
)

def qwen(model_name: Union[KnownModelName, str], settings: Optional[ModelSettings] = None) -> OpenAIModel:
    return OpenAIModel(str(model_name), provider=OpenAIProvider(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key=api_key,
    ), settings=settings)

