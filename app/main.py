import asyncio
import time
from math import ceil
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

from .requester import get_repos_io, read_dir, read_files


def create_app() -> FastAPI:
    app_ = FastAPI(
        title="Repo",
        description="Repo API",
        version="1.0.0",
    )
    return app_

app = create_app()

@app.middleware("http")
async def add_execution_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    end_time = time.time()

    execution_time = end_time - start_time
    response.headers["X-Timing"] = f"{execution_time:.2f} seconds"
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    status_code=500
    message = exec.message if hasattr(exc, 'message') else 'Internal server error. Please try again later.'
    if hasattr(exc, 'response') and hasattr(exc.response, 'status_code'):
        status_code = exc.response.status_code
    if hasattr(exc, 'status_code'):
        status_code = exc.status_code
    if hasattr(exc, 'status'):
        status_code = exc.status
    if hasattr(exc, 'response') and hasattr(exc.response, 'status'):
        status_code = exc.response.status

    return JSONResponse(
        status_code=status_code,
        content={"message": message},
    )

"""
Repository savings
"""
@app.post("/repositories/fetch", responses={
    427: {"description": "Requests limit exceeded"},
    429: {"description": "Too many requests"}
})
async def repo_fetch(count: int):
    if count <= 100:
        tasks = [get_repos_io(count, None)]
    else:
        pages = ceil(count / 100)
        tasks = [get_repos_io(count, page) for page in range(1, pages + 1)]

    await asyncio.gather(*tasks)
    return {"ok": "success"}

"""
Repository reading list
"""
@app.get("/repositories", responses={
    427: {"description": "Requests limit exceeded"},
    429: {"description": "Too many requests"}
})
async def repo_read():
    file_names = await read_dir()
    file_contents = await asyncio.gather(*[read_files(file_name) for file_name in file_names])
    return file_contents

"""
Repository reading list
"""
@app.get("/repositories/{name}", responses={
    427: {"description": "Requests limit exceeded"},
    429: {"description": "Too many requests"}
})
async def read_name(name: str):
    file_names = await read_dir(name)
    file_contents = await asyncio.gather(*[read_files(file_name, name) for file_name in file_names])
    return file_contents[0]
