import os
from langchain.chat_models import init_chat_model


def get_llm():
    llm = init_chat_model(
        api_key=os.getenv("MISTRAL"),
        model="mistral-large-latest",
        model_provider="mistralai",
    )
    return llm
