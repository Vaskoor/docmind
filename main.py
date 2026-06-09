from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os

from app.database import create_tables
from app.routers import auth, files, chatbots, users

# ── Create all DB tables on startup ──────────────────────────────────────────
create_tables()

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="DocMind API",
    description="AI Document Intelligence Platform — RAG Chatbot Builder",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(chatbots.router)
app.include_router(users.router)

# ── Static files ──────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Error Handlers ────────────────────────────────────────────────────────────
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    # For page routes, redirect to login on 401
    if exc.status_code == 401:
        return RedirectResponse(url="/login")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = " → ".join(str(e) for e in error["loc"] if e != "body")
        errors.append(f"{field}: {error['msg']}")
    return JSONResponse(
        status_code=422,
        content={"detail": "; ".join(errors)}
    )


# ── Page Routes (serve HTML) ──────────────────────────────────────────────────
def read_page(filename: str) -> str:
    path = os.path.join("static", "pages", filename)
    if not os.path.exists(path):
        return "<h1>Page not found</h1>"
    with open(path, "r") as f:
        return f.read()


@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(read_page("login.html"))


@app.get("/register", response_class=HTMLResponse)
async def register_page():
    return HTMLResponse(read_page("register.html"))


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    return HTMLResponse(read_page("dashboard.html"))


@app.get("/chatbots", response_class=HTMLResponse)
async def chatbots_page():
    return HTMLResponse(read_page("chatbots.html"))


@app.get("/account", response_class=HTMLResponse)
async def account_page():
    return HTMLResponse(read_page("user.html"))


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
