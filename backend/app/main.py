from scanner.repo_scanner import RepoScanner
from agents.file_classifier_agent import FileClassifierAgent
from dotenv import load_dotenv
import os

load_dotenv()

from langchain_mistralai import ChatMistralAI

PROJECT_PATH = r"D:\zovryn_assignment\frontend_mob"


def main():

    print("Scanning repo...")

    scanner = RepoScanner(PROJECT_PATH)

    files = scanner.scan()

    print(f"Found {len(files)} files")

    # send only metadata to LLM
    classifier = FileClassifierAgent(
        llm=ChatMistralAI(model="mistral-large-latest", api_key=os.getenv("MISTRAL"))
    )

    result = classifier.classify(files)

    print("\nMigration Context:")
    print(result.content)


if __name__ == "__main__":
    main()
