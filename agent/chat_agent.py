from pathlib import Path
from typing import Any, Dict
from analysis.chat import DatasetChat
from utils.exceptions import AIAgentError

class AIChatAgent:
    def __init__(self, dataset_path: Path):
        self.dataset_path = dataset_path
        self.chat = DatasetChat(self._load_dataset())

    def _load_dataset(self):
        from analysis.data_loader import DataLoader
        loader = DataLoader()
        return loader.load_dataset(self.dataset_path)

    def ask(self, question: str) -> Dict[str, Any]:
        try:
            return self.chat.answer(question)
        except Exception as exc:
            raise AIAgentError(f'Chat agent failed: {exc}') from exc
