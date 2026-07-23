import html
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd
import plotly.express as px

from analysis.data_loader import DataLoader
from analysis.summary import DatasetSummary
from analysis.cleaning import CleaningAnalyzer
from analysis.statistics import StatisticalAnalyzer

PLOTLY_CDN = 'https://cdn.plot.ly/plotly-2.32.0.min.js'

NUMERIC_STAT_ORDER = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
DISTRIBUTION_STAT_ORDER = ['mean', 'median', 'std', 'min', 'max', 'skew']


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _format_number(value: Any) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        if float(value).is_integer():
            return f'{int(value):,}'
        return f'{value:,.2f}'
    return _esc(value)


class ReportGenerator:
    def __init__(self):
        self.loader = DataLoader()

    def generate(self, dataset_path: Path, dataset_name: str) -> str:
        df = self.loader.load_dataset(dataset_path)
        summary = DatasetSummary(df).summary()
        cleaning = CleaningAnalyzer(df).cleaning_recommendations()
        statistics = StatisticalAnalyzer(df).distribution_summary()
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

        overview_cards = self._overview_cards(df, summary)
        schema_table = self._schema_table(summary['schema'])
        missing_table = self._missing_table(summary['missing_values'])
        numeric_table = self._numeric_summary_table(summary['numeric_summary'])
        categorical_section = self._categorical_section(summary['categorical_summary'])
        correlation_section = self._correlation_section(summary['correlation_matrix'])
        cleaning_section = self._cleaning_section(cleaning)
        distribution_table = self._distribution_table(statistics)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Dataset Report - {_esc(dataset_name)}</title>
<script src="{PLOTLY_CDN}"></script>
<style>{self._css()}</style>
</head>
<body>
<header class="hero">
    <h1>Dataset Analysis Report</h1>
    <p class="meta"><strong>Dataset:</strong> {_esc(dataset_name)} &nbsp;·&nbsp; <strong>Generated:</strong> {timestamp}</p>
</header>

<nav class="toc">
    <a href="#overview">Overview</a>
    <a href="#schema">Schema</a>
    <a href="#missing">Missing Values</a>
    <a href="#numeric">Numeric Summary</a>
    <a href="#categorical">Categorical</a>
    <a href="#correlation">Correlation</a>
    <a href="#cleaning">Cleaning</a>
    <a href="#distribution">Distribution</a>
</nav>

<main>
<section id="overview">
    <h2>Overview</h2>
    <div class="cards">{overview_cards}</div>
</section>

<section id="schema">
    <h2>Schema</h2>
    {schema_table}
</section>

<section id="missing">
    <h2>Missing Values</h2>
    {missing_table}
</section>

<section id="numeric">
    <h2>Numeric Summary</h2>
    {numeric_table}
</section>

<section id="categorical">
    <h2>Categorical Columns</h2>
    {categorical_section}
</section>

<section id="correlation">
    <h2>Correlation</h2>
    {correlation_section}
</section>

<section id="cleaning">
    <h2>Cleaning Recommendations</h2>
    {cleaning_section}
</section>

<section id="distribution">
    <h2>Statistical Distribution</h2>
    {distribution_table}
</section>
</main>

<footer>
    <p>Generated automatically by AI Data Analysis Platform.</p>
</footer>
</body>
</html>
'''

    # ---------- section builders ----------

    def _overview_cards(self, df: pd.DataFrame, summary: Dict[str, Any]) -> str:
        shape = summary['shape']
        missing = summary['missing_values']
        numeric_cols = len(summary['numeric_summary'])
        categorical_cols = len(summary['categorical_summary'].get('top_values', {}))
        duplicate_rows = int(df.duplicated().sum())
        total_cells = max(shape['rows'] * shape['columns'], 1)
        missing_pct = round((missing['total_missing'] / total_cells) * 100, 2)

        cards = [
            ('Rows', f"{shape['rows']:,}"),
            ('Columns', f"{shape['columns']:,}"),
            ('Missing Values', f"{missing['total_missing']:,} ({missing_pct}%)"),
            ('Duplicate Rows', f"{duplicate_rows:,}"),
            ('Numeric Columns', f'{numeric_cols:,}'),
            ('Categorical Columns', f'{categorical_cols:,}'),
        ]
        return ''.join(
            f'<div class="card"><div class="card-value">{_esc(value)}</div>'
            f'<div class="card-label">{_esc(label)}</div></div>'
            for label, value in cards
        )

    def _schema_table(self, schema: Dict[str, str]) -> str:
        rows = [(column, dtype) for column, dtype in schema.items()]
        return self._table(['Column', 'Type'], rows)

    def _missing_table(self, missing: Dict[str, Any]) -> str:
        by_column = missing['missing_by_column']
        percentage = missing['missing_percentage']
        flagged = sorted(
            ((col, count) for col, count in by_column.items() if count > 0),
            key=lambda item: item[1],
            reverse=True,
        )
        if not flagged:
            return '<p class="empty">No missing values detected.</p>'

        rows_html = ''.join(
            f'<tr><td>{_esc(col)}</td><td>{count:,}</td><td>{percentage.get(col, 0)}%'
            f'<div class="bar"><div class="bar-fill" style="width:{min(percentage.get(col, 0), 100)}%"></div></div>'
            f'</td></tr>'
            for col, count in flagged
        )
        return (
            '<table><thead><tr><th>Column</th><th>Missing Count</th><th>Missing %</th></tr></thead>'
            f'<tbody>{rows_html}</tbody></table>'
        )

    def _numeric_summary_table(self, numeric_summary: Dict[str, Any]) -> str:
        if not numeric_summary:
            return '<p class="empty">No numeric columns available.</p>'

        stats_present = [s for s in NUMERIC_STAT_ORDER if any(s in col_stats for col_stats in numeric_summary.values())]
        header = ['Column'] + [s.title() for s in stats_present]
        rows: List[Tuple[Any, ...]] = []
        for column, stats in numeric_summary.items():
            row = [column] + [_format_number(stats.get(stat, 0)) for stat in stats_present]
            rows.append(tuple(row))
        return self._table(header, rows, escape_first_col=True, pre_formatted=True)

    def _categorical_section(self, categorical_summary: Dict[str, Any]) -> str:
        top_values = categorical_summary.get('top_values', {})
        if not top_values:
            return '<p class="empty">No categorical columns available.</p>'

        blocks = []
        for column, values in top_values.items():
            rows = [(str(value), count) for value, count in values.items()]
            table = self._table(['Value', 'Count'], rows)
            blocks.append(f'<div class="subblock"><h3>{_esc(column)}</h3>{table}</div>')
        return f'<div class="grid-2">{"".join(blocks)}</div>'

    def _correlation_section(self, correlation_matrix: Dict[str, Any]) -> str:
        if not correlation_matrix or len(correlation_matrix) < 2:
            return '<p class="empty">Not enough numeric columns to compute correlations.</p>'

        corr_df = pd.DataFrame(correlation_matrix)
        fig = px.imshow(
            corr_df,
            text_auto='.2f',
            color_continuous_scale='RdBu_r',
            zmin=-1,
            zmax=1,
            aspect='auto',
        )
        fig.update_layout(margin=dict(l=40, r=40, t=20, b=40), height=min(120 * len(corr_df.columns), 700))
        chart_html = fig.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar': False})
        return f'<div class="chart">{chart_html}</div>'

    def _cleaning_section(self, cleaning: Dict[str, Any]) -> str:
        recommendations = cleaning.get('recommendations', [])
        rec_html = ''.join(f'<li>{_esc(item)}</li>' for item in recommendations)
        rec_block = f'<ul class="recommendations">{rec_html}</ul>'

        outliers = cleaning.get('outliers', {})
        if isinstance(outliers, dict) and 'message' in outliers:
            outlier_block = f'<p class="empty">{_esc(outliers["message"])}</p>'
        else:
            flagged = {
                col: detail for col, detail in outliers.items() if detail.get('outlier_count', 0) > 0
            }
            if not flagged:
                outlier_block = '<p class="empty">No significant outliers detected.</p>'
            else:
                rows = [
                    (
                        col,
                        f"{detail['outlier_count']:,}",
                        f"{detail['percentage']}%",
                        ', '.join(_format_number(v) for v in detail.get('sample_outliers', [])[:5]) or '—',
                    )
                    for col, detail in sorted(flagged.items(), key=lambda kv: kv[1]['outlier_count'], reverse=True)
                ]
                outlier_block = self._table(['Column', 'Outliers', '% of Values', 'Sample Values'], rows, pre_formatted=True)

        return f'{rec_block}<h3>Outlier Detection</h3>{outlier_block}'

    def _distribution_table(self, statistics: Dict[str, Any]) -> str:
        if 'message' in statistics:
            return f'<p class="empty">{_esc(statistics["message"])}</p>'

        stats_present = [s for s in DISTRIBUTION_STAT_ORDER if any(s in col_stats for col_stats in statistics.values())]
        header = ['Column'] + [s.title() for s in stats_present]
        rows = [
            tuple([column] + [_format_number(stats.get(stat, 0)) for stat in stats_present])
            for column, stats in statistics.items()
        ]
        return self._table(header, rows, pre_formatted=True)

    # ---------- generic helpers ----------

    def _table(
        self,
        headers: Iterable[str],
        rows: Iterable[Tuple[Any, ...]],
        escape_first_col: bool = True,
        pre_formatted: bool = False,
    ) -> str:
        rows = list(rows)
        if not rows:
            return '<p class="empty">No data available.</p>'

        head_html = ''.join(f'<th>{_esc(h)}</th>' for h in headers)
        body_rows = []
        for row in rows:
            cells = []
            for idx, value in enumerate(row):
                text = _esc(value) if (idx == 0 or not pre_formatted) else str(value)
                cells.append(f'<td>{text}</td>')
            body_rows.append(f'<tr>{"".join(cells)}</tr>')
        return f'<table><thead><tr>{head_html}</tr></thead><tbody>{"".join(body_rows)}</tbody></table>'

    def _css(self) -> str:
        return '''
:root { color-scheme: light; }
* { box-sizing: border-box; }
body {
    font-family: 'Segoe UI', Roboto, Arial, sans-serif;
    margin: 0;
    background: #f4f6f9;
    color: #1f2933;
    line-height: 1.55;
}
.hero {
    background: linear-gradient(135deg, #1f4e79, #2f7ec6);
    color: #fff;
    padding: 32px 40px;
}
.hero h1 { margin: 0 0 8px; font-size: 28px; }
.hero .meta { margin: 0; opacity: 0.9; font-size: 14px; }
nav.toc {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 18px;
    background: #fff;
    padding: 12px 40px;
    border-bottom: 1px solid #e2e8f0;
    position: sticky;
    top: 0;
    z-index: 10;
}
nav.toc a { color: #1f4e79; text-decoration: none; font-size: 13px; font-weight: 600; }
nav.toc a:hover { text-decoration: underline; }
main { max-width: 1080px; margin: 0 auto; padding: 24px 40px 60px; }
section { background: #fff; border-radius: 10px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08); }
h2 { color: #1f4e79; margin-top: 0; border-bottom: 2px solid #eef2f7; padding-bottom: 8px; }
h3 { color: #2f4f6f; margin: 16px 0 8px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px; }
.card { background: #f4f8fc; border: 1px solid #e0e9f2; border-radius: 8px; padding: 14px; text-align: center; }
.card-value { font-size: 22px; font-weight: 700; color: #1f4e79; }
.card-label { font-size: 12px; color: #64748b; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.04em; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { padding: 8px 10px; text-align: left; border-bottom: 1px solid #edf1f5; }
th { background: #f4f6f9; color: #334155; font-weight: 600; }
tbody tr:hover { background: #f8fafc; }
.bar { background: #edf1f5; border-radius: 4px; height: 6px; margin-top: 4px; overflow: hidden; }
.bar-fill { background: #e0762c; height: 100%; }
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }
.subblock { border: 1px solid #edf1f5; border-radius: 8px; padding: 12px; }
.recommendations { padding-left: 20px; }
.recommendations li { margin-bottom: 6px; }
.empty { color: #64748b; font-style: italic; }
.chart { overflow-x: auto; }
footer { text-align: center; color: #94a3b8; font-size: 12px; padding: 20px; }
'''
