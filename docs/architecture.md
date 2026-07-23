# Architecture Overview

The AI Data Analysis Platform uses a modular, layered structure designed for maintainability and scalability.

- `main.py`: Entry point and API orchestration layer.
- `utils/`: Shared configuration, centralized logging, exception classes, and helper utilities.
- `analysis/`: Dataset loading, summary statistics, cleaning recommendations, chat reasoning, and statistical analysis.
- `agent/`: High-level orchestration of AI-like services and feature-specific agents.
- `database/`: SQLite metadata storage for datasets and session tracking.
- `tools/`: File management and caching utilities used across the application.
- `visualization/`: Plotly-based visualization creation and chart recommendation logic.
- `reports/`: Report generation and export support.
- `ui/`: Static interface pages delivered by FastAPI.
