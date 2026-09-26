from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from routers import verify

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="RxGuard API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ALLOWED_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.include_router(verify.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}