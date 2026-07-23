from pathlib import Path
from typing import Any, Dict, Optional
from visualization.plots import VisualizationService
from visualization.recommendation import VisualizationRecommender
from utils.exceptions import VisualizationError

class VisualizationAgent:
    def __init__(self):
        self.service = VisualizationService()
        self.recommender = VisualizationRecommender()

    def recommend(self, df) -> Dict[str, Any]:
        return self.recommender.recommend(df)

    def plot(self, df, chart_type: str, x: Optional[str] = None, y: Optional[str] = None, color: Optional[str] = None) -> Dict[str, Any]:
        try:
            return self.service.create_plot(df, chart_type, x=x, y=y, color=color)
        except VisualizationError:
            raise
        except Exception as exc:
            raise VisualizationError(f'Unable to create plot: {exc}') from exc
