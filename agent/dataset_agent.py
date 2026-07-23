from pathlib import Path
from typing import Any, Dict
from analysis.data_loader import DataLoader
from analysis.summary import DatasetSummary
from analysis.cleaning import CleaningAnalyzer
from analysis.statistics import StatisticalAnalyzer
from analysis.transform import DatasetTransformer, describe_drop
from utils.exceptions import AIAgentError

class DatasetUnderstandingAgent:
    def __init__(self, loader: DataLoader = DataLoader()):
        self.loader = loader

    def analyze(self, dataset_path: Path) -> Dict[str, Any]:
        dataframe = self.loader.load_dataset(dataset_path)
        summary = DatasetSummary(dataframe)
        cleaning = CleaningAnalyzer(dataframe)
        stats = StatisticalAnalyzer(dataframe)
        return {
            'summary': summary.summary(),
            'cleaning': cleaning.cleaning_recommendations(),
            'statistics': {
                'distribution': stats.distribution_summary(),
                'correlation': stats.correlation_stats(),
                'feature_importance': stats.feature_importance(),
            },
        }


class DatasetEditAgent:
    def __init__(self, loader: DataLoader = DataLoader()):
        self.loader = loader

    def drop_last_column(self, dataset_path: Path) -> Dict[str, Any]:
        df = self.loader.load_dataset(dataset_path)
        transformed, dropped_column = DatasetTransformer(df).drop_last_column()
        return self._build_result(df, transformed, dropped_column)

    def drop_column(self, dataset_path: Path, column: str) -> Dict[str, Any]:
        df = self.loader.load_dataset(dataset_path)
        transformed = DatasetTransformer(df).drop_column(column)
        return self._build_result(df, transformed, column)

    def _build_result(self, before_df, after_df, dropped_column: str) -> Dict[str, Any]:
        return {
            'dataframe': after_df,
            'dropped_column': dropped_column,
            'report': describe_drop(before_df, after_df, dropped_column),
        }
