import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src import (HealthResponse, setup_logging, OutlierSettings, 
    ValidationSettings, MissingSettings, 
    ProcessingSettings, ProcessConfig, ProcessingReport, log_requests,
    MovieStorage,
    MovieUploadInfo,
    MovieDataResponse,
    MovieProcessingReport,
    MovieCache
)
from src.storage import MOVIE_COLUMNS
from data_pipeline import create_cleaning_report, process_data, validate_dataframe

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
storage = MovieStorage()
cache = MovieCache()

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return {"status": "ok", "version": "1.0.0"}



@app.post("/upload", response_model=MovieUploadInfo)
async def upload_movies(file: UploadFile = File(...)):


    """Read and store a CSV upload."""
    if Path(file.filename).suffix != ".csv":
        logger.warning(f"Uploaded File {file} is not supported CSV type")
        raise HTTPException( status_code=400, detail="Unsuported File Type")
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except (pd.errors.EmptyDataError,pd.errors.ParserError,UnicodeDecodeError) as error:
        logger.error(f"Unexpected Error Occured - {error}")
        raise HTTPException(status_code=400, detail=f"Unexpected {error} Occured")


    if set(df.columns) != set(MOVIE_COLUMNS):
        logger.error(f"columns {MOVIE_COLUMNS} required exactly, columns do not match exactly")
        raise HTTPException(status_code=400, detail=f"{list(df.columns)} does not match required columns {MOVIE_COLUMNS}")
    if df.empty:
        logger.error(f"table must contain at least one row")
        raise HTTPException(status_code=400, detail="table empty - must contain at least one row")
    
    df = df[MOVIE_COLUMNS]

    storage.save(df)
    cache.invalidate()
    logger.debug("caches cleared corrisponding to new db upload")

    logger.info(f"{file.filename} saved containing {df.shape[0]} rows")
    return MovieUploadInfo(
        filename=file.filename,
        rows=df.shape[0],
        columns=df.shape[1],
        column_names=list(df.columns)
    )



@app.get("/movies", response_model=MovieDataResponse)
def get_movies(limit: int = Query(default=100, ge=1)):
    # TODO 1: Look up the response using cache.get(limit).
    # If it is not None, log the cache hit at INFO and return it.

    #logger.info("VERY LOUND CANT MISS IT YELLING")
    cache_resp = cache.get(limit)
    if cache_resp is not None:
        logger.info(f"existing cache for limit of {limit} found")
        return cache_resp
    # Keep Part 1's SQL retrieval, total count, and response construction here.

    df = storage.get()
    if df.empty:
        logger.info("Movies table is empty")
        return {"data": [], "total_rows": 0}
    records = json.loads(df.head(limit).to_json(orient="records"))
    
    response = MovieDataResponse(
        data=records,
        total_rows=df.shape[0]
    )
    
    #2: Before the existing return, cache the complete response
    # using cache.set(limit, response).
    # Keep the existing row-count log and return.
    cache.set(limit, response.model_dump())
    logger.debug("cache created")

    logger.info(f"Total Row Count -- {df.shape[0]}")
    return response


@app.get("/movies/search", response_model=list[dict])
def query_movies(
    columns: list[str] = Query(default=["title"]),
    min_rating: float = Query(default=0, ge=0, le=10),
    limit: int = Query(default=100, ge=1)):
    # TODO: Call storage.query_movies(columns, min_rating, limit).
    # Catch ValueError and raise HTTPException with status 400.
    # Return id plus the selected fields, or [] if there are no matches.
    # Log the selected columns and returned row count at INFO.
    try:
        query = storage.query_movies(columns, min_rating, limit)
    except ValueError as error:
        logger.error(f"Unexpected Error Occured -- {error}")
        raise HTTPException(status_code=400, detail=f"Unexpected error occured -- {error}")
    logger.info(f'returned {len(query)} rows matching constraints, {["id"] + columns} returned for rows')
    return query



@app.post("/movies/process", response_model=MovieProcessingReport)
def process_movies(config: ProcessConfig):
    # TODO 1: Retrieve data using storage.get().
    # Raise HTTPException with status 400 if empty.
    df = storage.get()
    if df.empty:
        logger.error(f"table must contain at least one row")
        raise HTTPException(status_code=400, detail="table empty -- operation could not be performed")

    # TODO 2: Reuse MP2's configuration, validation, processing,
    # cleaning report, logging, and ValueError handling.
    config_dict = config.model_dump()
    required_columns = config_dict["validation"]["required_columns"]
    numeric_columns = config_dict["validation"]["numeric_columns"]

    exists = df.columns

    for elt in numeric_columns:
        if elt not in exists:
            raise HTTPException(status_code=400, detail=f"required column {elt} not found")
            logger.error(f"{elt} does not exist in dataframe")
    logger.info(f"All Required Columns Exist\n{numeric_columns}")

    try:
        df_val = (validate_dataframe(df, required_columns, numeric_columns)).copy()
        val_lines_removed = df.shape[0] - df_val.shape[0]
        logger.info(f"{val_lines_removed} rows removed in validation [containg null values]")

        df_proc = process_data(df_val, config_dict)
        clr_report = create_cleaning_report(df_val, df_proc)

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


    # TODO 3: Save the processed DataFrame using storage.save().
    # Return validation_rows_removed and cleaning_report without a dataset ID.
    storage.save(df_proc)
    logger.info("database updated using validation and cleaning configuration")
    cache.invalidate()
    logger.debug("caches cleared corrisponding to db update through processing")
    return MovieProcessingReport(
        validation_rows_removed=val_lines_removed,
        cleaning_report=clr_report)