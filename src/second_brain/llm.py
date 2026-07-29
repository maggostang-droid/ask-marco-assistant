"""Wählt das LLM aus, ohne einen Anbieter fest zu verdrahten.

init_chat_model() ist LangChains einheitliche Fabrik-Funktion: je nach
model_provider lädt sie im Hintergrund das passende Integrationspaket
(hier langchain-anthropic oder langchain-openai) und liefert in beiden
Fällen dasselbe Chat-Model-Interface zurück.
"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()


def get_llm() -> BaseChatModel:
    """Baut das Chat-Model aus LLM_PROVIDER/LLM_MODEL in der .env."""
    provider = os.environ.get("LLM_PROVIDER")
    model = os.environ.get("LLM_MODEL")

    if not provider or not model:
        raise RuntimeError(
            "LLM_PROVIDER und LLM_MODEL müssen in der .env gesetzt sein "
            "(siehe .env.example). Aktuell: "
            f"LLM_PROVIDER={provider!r}, LLM_MODEL={model!r}"
        )

    return init_chat_model(model, model_provider=provider)
