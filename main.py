from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from database.db import Database
from analysis.data_loader import DataLoader
from analysis.summary import DatasetSummary
from analysis.cleaning import CleaningAnalyzer
from analysis.statistics import StatisticalAnalyzer
from agent.chat_agent import AIChatAgent
from agent.visualization_agent import VisualizationAgent
from agent.report_agent import ReportAgent
from agent.dataset_agent import DatasetEditAgent
from tools.file_manager import save_upload_file, save_dataset, new_dataset_version_path
from utils.config import Config
from utils.logger import get_logger
from utils.exceptions import AppError, FileError, AnalysisError, VisualizationError, AIAgentError
from utils.helpers import ensure_directory

config = Config()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_directory(config.UPLOAD_DIR)
    ensure_directory(config.LOG_DIR)
    ensure_directory(config.REPORTS_DIR)
    app.state.db = Database()

    app.state.loader = DataLoader(config.UPLOAD_DIR)
    app.state.visualization = VisualizationAgent()
    app.state.report_agent = ReportAgent()
    app.state.edit_agent = DatasetEditAgent(app.state.loader)
    logger.info('AI Data Analysis Platform starting')
    yield
    logger.info('AI Data Analysis Platform stopping')

app = FastAPI(title='AI Data Analysis Platform', version='1.0.0', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.mount('/ui', StaticFiles(directory=config.UI_DIR), name='ui')


@app.get('/', response_class=HTMLResponse)
def root() -> RedirectResponse:
    return RedirectResponse(url='/ui/index.html')


@app.post('/api/upload')
async def upload_dataset(file: UploadFile = File(...)) -> JSONResponse:
    try:
        saved_path = save_upload_file(file, config.UPLOAD_DIR)
        dataset_id = uuid.uuid4().hex
        app.state.db.register_dataset(dataset_id, file.filename, str(saved_path), {'content_type': file.content_type})
        logger.info('Uploaded dataset %s to %s', file.filename, saved_path)
        return JSONResponse({'dataset_id': dataset_id, 'filename': file.filename, 'path': str(saved_path)})
    except FileError as exc:
        logger.error('Upload failed: %s', exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception('Unexpected upload error')
        raise HTTPException(status_code=500, detail='Unable to upload dataset.')


@app.get('/api/datasets')
def list_datasets() -> JSONResponse:
    datasets = app.state.db.list_datasets()
    return JSONResponse({'datasets': datasets})


@app.get('/api/datasets/{dataset_id}')
def get_dataset(dataset_id: str) -> JSONResponse:
    dataset = app.state.db.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found.')
    return JSONResponse(dataset)


@app.get('/api/datasets/{dataset_id}/preview')
def preview_dataset(dataset_id: str, rows: int = Query(10, ge=1, le=100)) -> JSONResponse:
    dataset = app.state.db.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found.')
    try:
        df = app.state.loader.preview_dataset(Path(dataset['path']), rows=rows)
        return JSONResponse({'preview': df.fillna('').to_dict(orient='records')})
    except FileError as exc:
        logger.error('Preview failed: %s', exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception('Preview error')
        raise HTTPException(status_code=500, detail='Unable to preview dataset.')


@app.get('/api/datasets/{dataset_id}/summary')
def dataset_summary(dataset_id: str) -> JSONResponse:
    dataset = app.state.db.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found.')
    try:
        df = app.state.loader.load_dataset(Path(dataset['path']))
        summary = DatasetSummary(df).summary()
        return JSONResponse({'summary': summary})
    except (FileError, AnalysisError) as exc:
        logger.error('Summary failed: %s', exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception('Summary error')
        raise HTTPException(status_code=500, detail='Unable to summarize dataset.')


@app.get('/api/datasets/{dataset_id}/analysis')
def dataset_analysis(dataset_id: str) -> JSONResponse:
    dataset = app.state.db.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found.')
    try:
        df = app.state.loader.load_dataset(Path(dataset['path']))
        summary = DatasetSummary(df).summary()
        cleaning = CleaningAnalyzer(df).cleaning_recommendations()
        statistics = StatisticalAnalyzer(df).distribution_summary()
        return JSONResponse({'summary': summary, 'cleaning': cleaning, 'statistics': statistics})
    except (FileError, AnalysisError) as exc:
        logger.error('Analysis failed: %s', exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception('Analysis error')
        raise HTTPException(status_code=500, detail='Unable to analyze dataset.')


def _save_dataset_version(dataset: dict, dataframe, dropped_column: str) -> dict:
    new_path = new_dataset_version_path(config.UPLOAD_DIR, dataset['filename'], f'no_{dropped_column}')
    save_dataset(dataframe, new_path)
    new_id = uuid.uuid4().hex
    app.state.db.register_dataset(
        new_id,
        new_path.name,
        str(new_path),
        {'parent_id': dataset['id'], 'operation': f"drop_column:{dropped_column}"},
    )
    return {'dataset_id': new_id, 'filename': new_path.name}


@app.post('/api/datasets/{dataset_id}/columns/drop-last')
def drop_last_column(dataset_id: str) -> JSONResponse:
    dataset = app.state.db.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found.')
    try:
        result = app.state.edit_agent.drop_last_column(Path(dataset['path']))
        version = _save_dataset_version(dataset, result['dataframe'], result['dropped_column'])
        logger.info('Dropped last column %s from dataset %s -> %s', result['dropped_column'], dataset_id, version['dataset_id'])
        return JSONResponse({
            'dataset_id': version['dataset_id'],
            'filename': version['filename'],
            'dropped_column': result['dropped_column'],
            'report': result['report'],
        })
    except (FileError, AnalysisError) as exc:
        logger.error('Drop last column failed: %s', exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception('Drop last column error')
        raise HTTPException(status_code=500, detail='Unable to modify dataset.')


@app.post('/api/datasets/{dataset_id}/columns/{column_name}/drop')
def drop_column(dataset_id: str, column_name: str) -> JSONResponse:
    dataset = app.state.db.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found.')
    try:
        result = app.state.edit_agent.drop_column(Path(dataset['path']), column_name)
        version = _save_dataset_version(dataset, result['dataframe'], result['dropped_column'])
        logger.info('Dropped column %s from dataset %s -> %s', column_name, dataset_id, version['dataset_id'])
        return JSONResponse({
            'dataset_id': version['dataset_id'],
            'filename': version['filename'],
            'dropped_column': result['dropped_column'],
            'report': result['report'],
        })
    except (FileError, AnalysisError) as exc:
        logger.error('Drop column failed: %s', exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception('Drop column error')
        raise HTTPException(status_code=500, detail='Unable to modify dataset.')


@app.get('/api/datasets/{dataset_id}/visualizations')
def visualization_recommendations(dataset_id: str) -> JSONResponse:
    dataset = app.state.db.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found.')
    try:
        df = app.state.loader.load_dataset(Path(dataset['path']))
        recommendations = app.state.visualization.recommend(df)
        return JSONResponse({'recommendations': recommendations})
    except Exception as exc:
        logger.exception('Visualization recommendation error')
        raise HTTPException(status_code=500, detail='Unable to generate visualization recommendations.')


@app.get('/api/datasets/{dataset_id}/visualization')
def generate_visualization(
    dataset_id: str,
    chart_type: str = Query('histogram'),
    x: str = Query(None),
    y: str = Query(None),
    color: str = Query(None),
) -> JSONResponse:
    dataset = app.state.db.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found.')
    try:
        df = app.state.loader.load_dataset(Path(dataset['path']))
        figure = app.state.visualization.plot(df, chart_type, x=x, y=y, color=color)
        return JSONResponse({'figure': figure})
    except VisualizationError as exc:
        logger.error('Visualization failed: %s', exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception('Visualization error')
        raise HTTPException(status_code=500, detail='Unable to create visualization.')


@app.post('/api/chat')
def ai_chat(dataset_id: str = Query(...), question: str = Query(...)) -> JSONResponse:
    dataset = app.state.db.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found.')
    try:
        chat_agent = AIChatAgent(Path(dataset['path']))
        result = chat_agent.ask(question)
        response: Dict[str, Any] = {
            'answer': result['text'],
            'figure': result.get('figure'),
            'chart_type': result.get('chart_type'),
        }
        edit = result.get('edit')
        if edit:
            version = _save_dataset_version(dataset, edit['dataframe'], edit['dropped_column'])
            response['dataset_id'] = version['dataset_id']
            response['filename'] = version['filename']
            logger.info(
                'Chat dropped column %s from dataset %s -> %s',
                edit['dropped_column'], dataset_id, version['dataset_id'],
            )
        return JSONResponse(response)
    except AIAgentError as exc:
        logger.error('Chat agent failed: %s', exc)
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception('Chat error')
        raise HTTPException(status_code=500, detail='Unable to answer question.')


@app.get('/api/datasets/{dataset_id}/report')
def report(dataset_id: str) -> HTMLResponse:
    dataset = app.state.db.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail='Dataset not found.')
    try:
        report_html = app.state.report_agent.create(Path(dataset['path']), dataset['filename'])
        return HTMLResponse(content=report_html, status_code=200)
    except Exception as exc:
        logger.exception('Report generation failed')
        raise HTTPException(status_code=500, detail='Unable to generate report.')


@app.get('/api/settings')
def settings() -> JSONResponse:
    return JSONResponse(
        {
            'upload_dir': str(config.UPLOAD_DIR),
            'log_dir': str(config.LOG_DIR),
            'db_path': str(config.DB_PATH),
            'allowed_extensions': list(config.ALLOWED_EXTENSIONS),
            'max_upload_size': config.MAX_UPLOAD_SIZE,
        }
    )


@app.exception_handler(AppError)
def app_error_handler(_, exc: AppError) -> JSONResponse:
    logger.error('Application error: %s', exc)
    return JSONResponse({'detail': str(exc)}, status_code=400)