"""
全局配置：路径、模型服务地址、开关。
所有存储目录在这里统一定义，其他模块引用。
"""
from pathlib import Path

# ── 基础目录 ──
BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"

# ── 各阶段产物目录 ──
ORIGINALS_DIR = STORAGE_DIR / "originals"   # 原始上传文件
PARSED_DIR = STORAGE_DIR / "parsed"         # 解析中间结果 Document IR
EXTRACTED_DIR = STORAGE_DIR / "extracted"   # STE/SGE 抽取结果
GRAPH_DIR = STORAGE_DIR / "graph"           # 知识图谱
META_DIR = STORAGE_DIR / "meta"             # 文档元数据
TASKS_DIR = STORAGE_DIR / "tasks"           # 任务状态
INDEX_DIR = STORAGE_DIR / "index"           # 持久化检索索引
REPORTS_DIR = STORAGE_DIR / "reports"       # 诊断和评估报告

# ── 模型服务（llama.cpp OpenAI 兼容接口）──
STE_URL = "http://localhost:8080/v1/chat/completions"   # Mistral-7B
SGE_URL = "http://localhost:8081/v1/chat/completions"   # Pixtral-12B
STE_MODEL = "mistral-7b"
SGE_MODEL = "pixtral-12b"
MODEL_TIMEOUT = 300

# 是否真实调用模型。False 时使用规则 mock，方便无 GPU 环境跑通 Demo
ENABLE_MODEL_CALL = True

# 启动时自动创建所有目录
for _d in [ORIGINALS_DIR, PARSED_DIR, EXTRACTED_DIR, GRAPH_DIR, META_DIR, TASKS_DIR, INDEX_DIR, REPORTS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)
