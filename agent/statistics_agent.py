from pathlib import Path
from typing import Dict
from analysis.statistics import StatisticalAnalyzer

class StatisticsAgent:
    def __init__(self, dataset_path: Path):
        from analysis.data_loader import DataLoader
        loader = DataLoader()
        self.df = loader.load_dataset(dataset_path)
        self.analyzer = StatisticalAnalyzer(self.df)

    def summary(self) -> Dict[str, Dict]:
        return {
            'distribution': self.analyzer.distribution_summary(),
            'correlation': self.analyzer.correlation_stats(),
            'feature_importance': self.analyzer.feature_importance(),
        }
