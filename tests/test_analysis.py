import pytest
import pandas as pd
from analysis.summary import DatasetSummary
from analysis.cleaning import CleaningAnalyzer
from analysis.statistics import StatisticalAnalyzer
from analysis.chat import DatasetChat
from analysis.transform import DatasetTransformer
from utils.exceptions import AnalysisError


def test_dataset_summary_basic_metrics() -> None:
    df = pd.DataFrame({
        'age': [20, 30, 40],
        'income': [50000, 60000, 70000],
        'city': ['A', 'B', 'A'],
    })
    summary = DatasetSummary(df).summary()
    assert summary['shape']['rows'] == 3
    assert summary['shape']['columns'] == 3
    assert 'age' in summary['schema']


def test_cleaning_analyzer_recommends_no_issues() -> None:
    df = pd.DataFrame({'value': [1, 2, 3]})
    result = CleaningAnalyzer(df).cleaning_recommendations()
    assert 'clean' in result['recommendations'][0].lower()


def test_statistical_analyzer_returns_distribution() -> None:
    df = pd.DataFrame({'x': [1, 2, 3, 4]})
    stats = StatisticalAnalyzer(df).distribution_summary()
    assert 'mean' in stats['x']


def test_dataset_chat_handles_summary_question() -> None:
    df = pd.DataFrame({'x': [1, 2, 3], 'category': ['A', 'B', 'A']})
    result = DatasetChat(df).answer('Provide a summary')
    assert 'Dataset contains' in result['text']
    assert result['figure'] is None


def test_dataset_chat_builds_chart_for_visualization_request() -> None:
    df = pd.DataFrame({'x': [1, 2, 3, 4], 'y': [4, 3, 2, 1]})
    result = DatasetChat(df).answer('Show me a scatter chart of x and y')
    assert result['chart_type'] == 'scatter'
    assert result['figure'] is not None


def test_transformer_drops_last_column() -> None:
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4], 'c': [5, 6]})
    transformed, dropped = DatasetTransformer(df).drop_last_column()
    assert dropped == 'c'
    assert list(transformed.columns) == ['a', 'b']


def test_transformer_drops_named_column() -> None:
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    transformed = DatasetTransformer(df).drop_column('a')
    assert list(transformed.columns) == ['b']


def test_transformer_rejects_unknown_column() -> None:
    df = pd.DataFrame({'a': [1, 2]})
    with pytest.raises(AnalysisError):
        DatasetTransformer(df).drop_column('missing')


def test_transformer_rejects_dropping_only_column() -> None:
    df = pd.DataFrame({'a': [1, 2]})
    with pytest.raises(AnalysisError):
        DatasetTransformer(df).drop_last_column()


def test_dataset_chat_deletes_last_column() -> None:
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4], 'c': [5, 6]})
    result = DatasetChat(df).answer('Please delete the last column')
    assert result['edit'] is not None
    assert result['edit']['dropped_column'] == 'c'
    assert list(result['edit']['dataframe'].columns) == ['a', 'b']


def test_dataset_chat_deletes_named_column() -> None:
    df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
    result = DatasetChat(df).answer('Remove the a column please')
    assert result['edit'] is not None
    assert result['edit']['dropped_column'] == 'a'


def test_dataset_chat_edit_without_target_asks_for_column() -> None:
    df = pd.DataFrame({'age': [1, 2], 'income': [3, 4]})
    result = DatasetChat(df).answer('Please delete a column')
    assert result['edit'] is None
    assert 'which column' in result['text'].lower()


def test_dataset_chat_combines_delete_and_visualization() -> None:
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [3, 2, 1], 'c': [5, 6, 7]})
    result = DatasetChat(df).answer('Delete the last column and show the visualisation of columns')
    assert result['edit'] is not None
    assert result['edit']['dropped_column'] == 'c'
    assert result['figure'] is not None
    assert result['chart_type'] is not None
