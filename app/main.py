from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.common.config import settings
from app.common.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=auth_router)

@app.get("/health")
async def health():
    return {"status": "ok"}