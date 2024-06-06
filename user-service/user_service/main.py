from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield


app = FastAPI(lifespan=lifespan, title="User Service", version='1.0.0')


@app.get('/user')
async def root() -> Any:
    return {"message": "Welcome User"}