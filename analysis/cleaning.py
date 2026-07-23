from typing import Any, Dict
import pandas as pd
from utils.exceptions import AnalysisError

class CleaningAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def missing_value_summary(self) -> Dict[str, Any]:
        missing = self.df.isna().sum()
        total = len(self.df)
        return {
            'missing_counts': missing.to_dict(),
            'missing_percent': ((missing / max(total, 1)) * 100).round(2).to_dict(),
            'columns_with_missing': missing[missing > 0].index.tolist(),
        }

    def outlier_detection(self) -> Dict[str, Any]:
        numeric = self.df.select_dtypes(include='number')
        if numeric.empty:
            return {'message': 'No numeric columns to analyze for outliers.'}

        outlier_summary = {}
        for column in numeric.columns:
            values = numeric[column].dropna()
            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = values[(values < lower) | (values > upper)]
            outlier_summary[column] = {
                'outlier_count': int(outliers.count()),
                'percentage': float(round((outliers.count() / max(len(values), 1)) * 100, 2)),
                'sample_outliers': outliers.head(5).tolist(),
            }
        return outlier_summary

    def cleaning_recommendations(self) -> Dict[str, Any]:
        missing = self.missing_value_summary()
        outliers = self.outlier_detection()
        recommendations = []
        if missing['columns_with_missing']:
            recommendations.append(
                f"Review missing values in columns: {', '.join(missing['columns_with_missing'])}."
            )
        if isinstance(outliers, dict) and outliers:
            outlier_cols = [column for column, detail in outliers.items() if detail.get('outlier_count', 0) > 0]
            if outlier_cols:
                recommendations.append(
                    f"Check outlier values in numeric columns: {', '.join(outlier_cols)}."
                )
        if not recommendations:
            recommendations.append('Dataset appears clean based on missing value and outlier checks.')
        return {'recommendations': recommendations, 'missing': missing, 'outliers': outliers}
