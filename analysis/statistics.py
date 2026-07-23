from typing import Any, Dict
import pandas as pd

class StatisticalAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def distribution_summary(self) -> Dict[str, Any]:
        numeric = self.df.select_dtypes(include='number')
        if numeric.empty:
            return {'message': 'No numeric columns available for distribution analysis.'}
        summary = numeric.agg(['mean', 'median', 'std', 'min', 'max', 'skew']).fillna(0).to_dict()
        return summary

    def correlation_stats(self) -> Dict[str, Any]:
        numeric = self.df.select_dtypes(include='number')
        if numeric.empty or numeric.shape[1] < 2:
            return {'message': 'Insufficient numeric columns to generate correlation statistics.'}
        matrix = numeric.corr().fillna(0).to_dict()
        return {'correlation_matrix': matrix}

    def feature_importance(self) -> Dict[str, Any]:
        numeric = self.df.select_dtypes(include='number')
        if numeric.empty:
            return {'message': 'No numeric features available for importance analysis.'}
        correlations = numeric.corr().abs().mean().sort_values(ascending=False).to_dict()
        return {'feature_importance': correlations}
