from typing import Any, Dict
import pandas as pd
from utils.exceptions import AnalysisError

class DatasetSummary:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def shape(self) -> Dict[str, int]:
        return {'rows': int(self.df.shape[0]), 'columns': int(self.df.shape[1])}

    def schema(self) -> Dict[str, str]:
        return {column: str(dtype) for column, dtype in self.df.dtypes.items()}

    def missing_values(self) -> Dict[str, Any]:
        missing_count = self.df.isna().sum()
        missing_percent = (missing_count / max(len(self.df), 1)) * 100
        return {
            'total_missing': int(missing_count.sum()),
            'missing_by_column': missing_count.to_dict(),
            'missing_percentage': missing_percent.round(2).to_dict(),
        }

    def numeric_summary(self) -> Dict[str, Any]:
        try:
            numeric = self.df.select_dtypes(include='number')
            return numeric.describe().fillna(0).to_dict()
        except Exception as exc:
            raise AnalysisError(f'Numeric summary failed: {exc}') from exc

    def categorical_summary(self) -> Dict[str, Any]:
        categorical = self.df.select_dtypes(include=['object', 'category', 'bool'])
        top_values = {}
        for column in categorical.columns:
            counts = categorical[column].value_counts(dropna=False).head(5)
            top_values[column] = {
                (str(value) if pd.notna(value) else None): int(count)
                for value, count in counts.items()
            }
        return {'top_values': top_values}

    def correlation_matrix(self) -> Dict[str, Any]:
        numeric = self.df.select_dtypes(include='number')
        if numeric.empty:
            return {}
        return numeric.corr().fillna(0).to_dict()

    def summary(self) -> Dict[str, Any]:
        return {
            'shape': self.shape(),
            'schema': self.schema(),
            'missing_values': self.missing_values(),
            'numeric_summary': self.numeric_summary(),
            'categorical_summary': self.categorical_summary(),
            'correlation_matrix': self.correlation_matrix(),
        }
