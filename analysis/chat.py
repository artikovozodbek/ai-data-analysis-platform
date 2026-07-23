from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from analysis.summary import DatasetSummary
from analysis.transform import DatasetTransformer, describe_drop
from visualization.plots import VisualizationService
from utils.exceptions import AIAgentError, AnalysisError, VisualizationError

VISUALIZATION_TRIGGERS = (
    'chart', 'plot', 'graph', 'grafik', 'chiz', 'vizual', 'visual', 'diagram',
    'histogram', 'scatter', 'heatmap', 'boxplot', 'draw',
)

EDIT_ACTION_WORDS = ('delete', 'remove', 'drop', "o'chir", 'ochir', 'olib tashla', 'chiqarib tashla')
EDIT_TARGET_WORDS = ('column', 'ustun', 'ustunni', 'ustuni')
LAST_COLUMN_PHRASES = ('last column', 'oxirgi ustun', "so'nggi ustun", 'songgi ustun', 'oxirgisi')

CHART_TYPE_KEYWORDS: List[Tuple[str, str]] = [
    ('heatmap', 'heatmap'),
    ('correlation', 'heatmap'),
    ('missing', 'missing'),
    ('importance', 'feature_importance'),
    ('histogram', 'histogram'),
    ('distribution', 'histogram'),
    ('scatter', 'scatter'),
    ('relationship', 'scatter'),
    ('outlier', 'box'),
    ('box', 'box'),
    ('pie', 'pie'),
    ('bar', 'bar'),
    ('trend', 'line'),
    ('line', 'line'),
]

CHART_REQUIRES_XY = {'scatter', 'line'}
CHART_REQUIRES_X = {'histogram', 'box', 'bar', 'pie'}


class DatasetChat:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.summary = DatasetSummary(df)
        self.visualizer = VisualizationService()

    def answer(self, question: str) -> Dict[str, Any]:
        if not question:
            raise AIAgentError('Question cannot be empty.')

        text = question.strip().lower()
        wants_edit = self._wants_edit(text)
        wants_chart = any(keyword in text for keyword in VISUALIZATION_TRIGGERS)

        if not wants_edit and not wants_chart:
            return {'text': self._answer_text(text), 'figure': None, 'chart_type': None, 'edit': None}

        text_parts = []
        edit_payload = None
        working_df = self.df

        if wants_edit:
            edit_result = self._build_edit(text)
            text_parts.append(edit_result['text'])
            edit_payload = edit_result.get('edit')
            if edit_payload:
                working_df = edit_payload['dataframe']

        if wants_chart:
            chart_result = self._build_visualization(text, working_df)
            text_parts.append(chart_result['text'])
            figure = chart_result.get('figure')
            chart_type = chart_result.get('chart_type')
        else:
            figure = None
            chart_type = None

        return {'text': ' '.join(text_parts), 'figure': figure, 'chart_type': chart_type, 'edit': edit_payload}

    # ---------- text answers ----------

    def _answer_text(self, text: str) -> str:
        if 'missing' in text:
            missing = self.summary.missing_values()
            return (
                f"The dataset contains {missing['total_missing']} missing values. "
                f"Columns with missing values: {', '.join([k for k, v in missing['missing_by_column'].items() if v > 0])}."
            )

        if 'correlation' in text:
            matrix = self.summary.correlation_matrix()
            if not matrix:
                return 'No numeric columns available to compute correlations.'
            top_correlations = []
            for column, row in matrix.items():
                for target, value in row.items():
                    if column != target and abs(value) >= 0.7:
                        top_correlations.append(f'{column} and {target}: {round(value,2)}')
            if top_correlations:
                return 'Strong correlations found: ' + '; '.join(top_correlations[:5])
            return 'No strong correlations detected in numeric columns.'

        if 'summary' in text or 'overview' in text or 'tell me about' in text or 'about this dataset' in text or 'about the dataset' in text:
            shape = self.summary.shape()
            return (
                f"Dataset contains {shape['rows']} rows and {shape['columns']} columns. "
                f"Top columns: {', '.join(self.df.columns[:5].astype(str))}."
            )

        if 'top' in text or 'largest' in text or 'highest' in text:
            numeric = self.df.select_dtypes(include='number')
            if numeric.empty:
                return 'No numeric columns available to identify top values.'
            top_column = numeric.mean().sort_values(ascending=False).index[0]
            top_value = numeric[top_column].max()
            return f"The column with the highest average is {top_column} with a maximum value of {top_value}."

        if 'column' in text and ('list' in text or 'name' in text or 'show' in text or 'what are' in text or 'which' in text):
            columns = ', '.join(str(c) for c in self.df.columns)
            return f"The dataset has {len(self.df.columns)} columns: {columns}."

        return (
            'I can help analyze missing values, correlations, provide a summary, or build a chart. '
            'Ask about missing values, correlation, dataset summary, or say "show me a chart of <column>".'
        )

    # ---------- visualization answers ----------

    def _build_visualization(self, text: str, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        df = self.df if df is None else df
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
        mentioned_numeric = [c for c in numeric_cols if c.lower() in text]
        mentioned_categorical = [c for c in categorical_cols if c.lower() in text]

        chart_type = next((ctype for keyword, ctype in CHART_TYPE_KEYWORDS if keyword in text), None)
        if chart_type is None:
            chart_type = self._infer_chart_type(numeric_cols, categorical_cols, mentioned_numeric, mentioned_categorical)
        if chart_type is None:
            return {'text': 'The dataset has no columns available to visualize.', 'figure': None, 'chart_type': None, 'edit': None}

        x, y, color = self._pick_columns(chart_type, numeric_cols, categorical_cols, mentioned_numeric, mentioned_categorical)

        if chart_type in CHART_REQUIRES_XY and (not x or not y):
            return {
                'text': f"I need two numeric columns to build a {chart_type} chart. "
                        f"Try mentioning column names, e.g. 'scatter of {numeric_cols[0]} and {numeric_cols[1]}'." if len(numeric_cols) >= 2
                        else f'Not enough numeric columns available for a {chart_type} chart.',
                'figure': None,
                'chart_type': None,
                'edit': None,
            }
        if chart_type in CHART_REQUIRES_X and not x:
            return {'text': f'I could not find a suitable column to build a {chart_type} chart.', 'figure': None, 'chart_type': None, 'edit': None}

        try:
            figure = self.visualizer.create_plot(df, chart_type, x=x, y=y, color=color)
        except VisualizationError as exc:
            return {'text': f"Couldn't build a {chart_type} chart: {exc}", 'figure': None, 'chart_type': None, 'edit': None}

        return {'text': self._describe_chart(chart_type, x, y, color), 'figure': figure, 'chart_type': chart_type, 'edit': None}

    def _infer_chart_type(
        self,
        numeric_cols: List[str],
        categorical_cols: List[str],
        mentioned_numeric: List[str],
        mentioned_categorical: List[str],
    ) -> Optional[str]:
        if len(mentioned_numeric) >= 2:
            return 'scatter'
        if mentioned_categorical:
            return 'bar'
        if mentioned_numeric:
            return 'histogram'
        if len(numeric_cols) >= 2:
            return 'heatmap'
        if numeric_cols:
            return 'histogram'
        if categorical_cols:
            return 'bar'
        return None

    def _pick_columns(
        self,
        chart_type: str,
        numeric_cols: List[str],
        categorical_cols: List[str],
        mentioned_numeric: List[str],
        mentioned_categorical: List[str],
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        x = y = color = None

        if chart_type in ('scatter', 'line'):
            pool = list(dict.fromkeys(mentioned_numeric + [c for c in numeric_cols if c not in mentioned_numeric]))
            if len(pool) >= 2:
                x, y = pool[0], pool[1]
            color = mentioned_categorical[0] if mentioned_categorical and chart_type == 'scatter' else None
        elif chart_type == 'histogram':
            pool = mentioned_numeric or numeric_cols
            x = pool[0] if pool else None
            color = mentioned_categorical[0] if mentioned_categorical else None
        elif chart_type == 'box':
            pool = mentioned_numeric or numeric_cols
            if mentioned_categorical:
                x = mentioned_categorical[0]
                y = pool[0] if pool else None
            else:
                x = pool[0] if pool else None
        elif chart_type in ('bar', 'pie'):
            x = mentioned_categorical[0] if mentioned_categorical else (categorical_cols[0] if categorical_cols else None)
            if chart_type == 'pie':
                pool = mentioned_numeric or numeric_cols
                y = pool[0] if pool else None

        return x, y, color

    def _describe_chart(self, chart_type: str, x: Optional[str], y: Optional[str], color: Optional[str]) -> str:
        color_note = f', colored by {color}' if color else ''
        if chart_type == 'heatmap':
            return 'Here is the correlation heatmap for the numeric columns.'
        if chart_type == 'missing':
            return 'Here is the missing value breakdown by column.'
        if chart_type == 'feature_importance':
            return 'Here is the feature importance chart based on average absolute correlation.'
        if chart_type == 'histogram':
            return f'Here is a histogram of {x}{color_note}.'
        if chart_type == 'scatter':
            return f'Here is a scatter plot of {x} vs {y}{color_note}.'
        if chart_type == 'line':
            return f'Here is a line chart of {x} vs {y}.'
        if chart_type == 'box':
            return f'Here is a box plot of {y} by {x}.' if y else f'Here is a box plot of {x}.'
        if chart_type == 'bar':
            return f'Here is a bar chart of {x}.'
        if chart_type == 'pie':
            return f'Here is a pie chart of {x}.'
        return f'Here is a {chart_type} chart.'

    # ---------- edit (dataset modification) answers ----------

    def _wants_edit(self, text: str) -> bool:
        has_action = any(word in text for word in EDIT_ACTION_WORDS)
        has_target = any(word in text for word in EDIT_TARGET_WORDS) or any(phrase in text for phrase in LAST_COLUMN_PHRASES)
        return has_action and has_target

    def _build_edit(self, text: str) -> Dict[str, Any]:
        columns = list(self.df.columns)
        target: Optional[str] = None

        if any(phrase in text for phrase in LAST_COLUMN_PHRASES):
            target = columns[-1] if columns else None
        else:
            matches = [c for c in columns if c.lower() in text]
            if matches:
                target = max(matches, key=len)

        if not target:
            return {
                'text': "Please tell me which column to delete, e.g. \"delete the Legendary column\" or \"delete the last column\".",
                'figure': None,
                'chart_type': None,
                'edit': None,
            }

        try:
            transformed = DatasetTransformer(self.df).drop_column(target)
        except AnalysisError as exc:
            return {'text': str(exc), 'figure': None, 'chart_type': None, 'edit': None}

        report = describe_drop(self.df, transformed, target)
        return {
            'text': report,
            'figure': None,
            'chart_type': None,
            'edit': {'operation': 'drop_column', 'dropped_column': target, 'dataframe': transformed},
        }
