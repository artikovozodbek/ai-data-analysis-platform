import json
from typing import Any, Dict, Optional
from pathlib import Path
import plotly.express as px
from plotly.graph_objs import Figure
from utils.exceptions import VisualizationError
import pandas as pd

class VisualizationService:
    def create_plot(
        self,
        df: pd.DataFrame,
        chart_type: str,
        x: Optional[str] = None,
        y: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Dict[str, Any]:
        if df.empty:
            raise VisualizationError('Dataset contains no data.')

        valid = df.dropna(subset=[col for col in [x, y, color] if col is not None], how='any')

        try:
            if chart_type == 'histogram':
                if not x:
                    raise VisualizationError('Histogram requires an x column.')
                fig = px.histogram(valid, x=x, color=color)
            elif chart_type == 'scatter':
                if not x or not y:
                    raise VisualizationError('Scatter plot requires x and y columns.')
                fig = px.scatter(valid, x=x, y=y, color=color)
            elif chart_type == 'box':
                if not x:
                    raise VisualizationError('Box plot requires an x column.')
                fig = px.box(valid, x=x, y=y, color=color)
            elif chart_type == 'line':
                if not x or not y:
                    raise VisualizationError('Line plot requires x and y columns.')
                fig = px.line(valid, x=x, y=y, color=color)
            elif chart_type == 'pie':
                if not x:
                    raise VisualizationError('Pie chart requires an x column.')
                fig = px.pie(valid, names=x, values=y if y else None)
            elif chart_type == 'bar':
                if not x:
                    raise VisualizationError('Bar plot requires an x column.')
                fig = px.bar(valid, x=x, y=y, color=color)
            elif chart_type == 'heatmap':
                numeric = df.select_dtypes(include='number')
                if numeric.empty:
                    raise VisualizationError('Heatmap requires numeric data.')
                corr = numeric.corr()
                fig = px.imshow(corr, text_auto=True)
            elif chart_type == 'missing':
                missing = df.isna().mean() * 100
                fig = px.bar(x=missing.index.tolist(), y=missing.values, labels={'x': 'Column', 'y': 'Missing %'})
            elif chart_type == 'feature_importance':
                numeric = df.select_dtypes(include='number')
                if numeric.empty:
                    raise VisualizationError('Feature importance requires numeric data.')
                importance = numeric.corr().abs().mean().sort_values(ascending=False)
                fig = px.bar(x=importance.index.tolist(), y=importance.values, labels={'x': 'Feature', 'y': 'Importance'})
            else:
                raise VisualizationError(f'Unsupported chart type: {chart_type}')

            return json.loads(fig.to_json())
        except Exception as exc:
            raise VisualizationError(f'Visualization generation failed: {exc}') from exc
