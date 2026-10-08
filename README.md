# 工业智能维保多 Agent 系统

本项目面向本地/内网工业维保场景：上传任意设备手册或现场文档，解析 Agent 建立统一 Document IR、实体关系和持久化索引；诊断 Agent 使用症状标准化、BM25/轻量混合召回、知识图谱证据和实时点位排除，输出带页码/来源的候选原因；评估 Agent 对测试集做可复现评估。

## 启动

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

模型服务不可用时，解析与诊断会自动使用规则 mock；若已安装本地 llama.cpp，可继续使用 `scripts/start_model_services.ps1`。

## API

- `POST /api/v1/upload/` 上传 PDF、图片、DOCX、XLSX 或 ZIP
- `POST /api/v1/diagnosis/`：`{"symptom":"起升机构动作异常","device_id":"CRANE-01"}`
- `POST /api/v1/evaluation/run`：运行 `tests/data/diagnosis.jsonl`
- `GET /docs` 查看 OpenAPI

索引、原始文件、IR、抽取结果、图谱、诊断和评估报告均落盘到 `storage/`，适用于更换行业、设备和手册，不依赖固定关键词集合。
