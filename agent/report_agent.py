from pathlib import Path
from typing import Any, Dict
from reports.generator import ReportGenerator

class ReportAgent:
    def __init__(self):
        self.generator = ReportGenerator()

    def create(self, dataset_path: Path, dataset_name: str) -> str:
        return self.generator.generate(dataset_path, dataset_name)
