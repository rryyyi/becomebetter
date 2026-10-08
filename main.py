"""FastAPI 入口"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from routers import upload, parse, documents, diagnosis, evaluation

app = FastAPI(title="工业智能维保多 Agent 系统", version="2.0")

# 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(upload.router)
app.include_router(parse.router)
app.include_router(documents.router)
app.include_router(diagnosis.router)
app.include_router(evaluation.router)


@app.get("/")
async def root():
    """返回前端页面"""
    return FileResponse(Path(__file__).parent / "frontend" / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}
