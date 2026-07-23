from typing import Any, Dict
import pandas as pd

class VisualizationRecommender:
    def recommend(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {'recommendations': ['Dataset is empty. Upload a dataset to receive visualization recommendations.']}

        numeric = df.select_dtypes(include='number')
        categorical = df.select_dtypes(include=['object', 'category', 'bool'])
        recommendations = []

        if not numeric.empty:
            recommendations.extend(['histogram', 'box', 'line', 'scatter', 'heatmap', 'feature_importance'])

        if not categorical.empty:
            recommendations.extend(['bar', 'pie'])

        if df.isna().any().any():
            recommendations.append('missing')

        return {
            'recommendations': list(dict.fromkeys(recommendations)),
            'numeric_columns': numeric.columns.tolist(),
            'categorical_columns': categorical.columns.tolist(),
        }
