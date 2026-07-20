import os
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()


def get_llm():
    llm = init_chat_model(
        api_key=os.getenv("MISTRAL"),
        model="mistral-small-latest",
        model_provider="mistralai",
    )
    return llm
