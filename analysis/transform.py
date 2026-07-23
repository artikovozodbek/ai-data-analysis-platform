from typing import Tuple
import pandas as pd
from analysis.summary import DatasetSummary
from utils.exceptions import AnalysisError


class DatasetTransformer:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def drop_column(self, column: str) -> pd.DataFrame:
        if column not in self.df.columns:
            raise AnalysisError(f"Column '{column}' not found in dataset.")
        if self.df.shape[1] <= 1:
            raise AnalysisError('Cannot drop the only remaining column.')
        return self.df.drop(columns=[column])

    def drop_last_column(self) -> Tuple[pd.DataFrame, str]:
        if self.df.shape[1] <= 1:
            raise AnalysisError('Cannot drop the only remaining column.')
        last_column = self.df.columns[-1]
        return self.drop_column(last_column), last_column


def describe_drop(before_df: pd.DataFrame, after_df: pd.DataFrame, dropped_column: str) -> str:
    before = DatasetSummary(before_df).summary()
    after = DatasetSummary(after_df).summary()
    before_missing = before['missing_values']['total_missing']
    after_missing = after['missing_values']['total_missing']
    if before_missing != after_missing:
        missing_note = (
            f"Missing values dropped from {before_missing} to {after_missing}, "
            f"since '{dropped_column}' accounted for {before_missing - after_missing} of them."
        )
    else:
        missing_note = f'Total missing values remain unchanged at {after_missing}.'

    remaining_columns = ', '.join(str(c) for c in after_df.columns)
    return (
        f"Removed column '{dropped_column}' (type: {before['schema'].get(dropped_column, 'unknown')}). "
        f"Dataset shape changed from {before['shape']['rows']} rows x {before['shape']['columns']} columns "
        f"to {after['shape']['rows']} rows x {after['shape']['columns']} columns. "
        f"{missing_note} "
        f"Remaining columns: {remaining_columns}."
    )
