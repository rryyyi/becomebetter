"""FastAPI 入口"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from routers import upload, parse, documents

app = FastAPI(title="SPE 文件解析 Demo", version="1.0")

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


@app.get("/")
async def root():
    """返回前端页面"""
    return FileResponse(Path(__file__).parent / "frontend" / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}