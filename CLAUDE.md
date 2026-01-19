# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

财报分析助手 Agent - 一个学习型项目，既是真实可用的 Agent，也是学习 Agent 架构的教学项目。

**当前进度**: 全部完成
- [x] 阶段1-2: 基础 Agent 实现（Tool Use + ReAct 循环）
- [x] 阶段3: RAG 集成（文档加载、切分、向量存储、检索）
- [x] 阶段4: 完善功能（CLI、答案生成、测试）

## Development Commands

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 设置 OPENAI_API_KEY

# 运行 CLI（推荐）
python -m src.interface.cli

# 运行模块测试
python -m src.agent.simple_agent      # 单次工具调用 Agent
python -m src.agent.orchestrator      # ReAct 循环 Agent
python -m src.tools.base              # 工具注册表测试
python -m src.tools.calculator        # 计算器工具测试

# 运行实验脚本
python experiments/06_rag_agent.py    # 完整 RAG Agent 演示

# 运行单元测试
pytest tests/ -v
```

## Architecture

```
用户输入 → CLI层 → Agent决策层(ReAct循环) → 工具层 → 输出
                          ↓↑
                   知识索引层 ← 文档摄取层
```

### 已实现模块

**接口层 (`src/interface/`)**:
- `cli.py`: 命令行交互界面（REPL 风格）
- `session.py`: 会话管理（保存/加载对话历史）

**Agent 层 (`src/agent/`)**:
- `simple_agent.py`: 单次工具调用，理解 Tool Use 的起点
- `orchestrator.py`: 完整 ReAct 循环，支持多轮工具调用

**工具层 (`src/tools/`)**:
- `base.py`: `Tool` 抽象基类 + `ToolRegistry` 工具注册表
- `calculator.py`: 数学表达式计算工具
- `retrieval.py`: 语义检索工具（连接向量数据库）

**摄取层 (`src/ingestion/`)**:
- `loader.py`: 文档加载器（PDF/TXT）
- `chunker.py`: 文档切分器（支持重叠）

**索引层 (`src/index/`)**:
- `embedder.py`: Embedding 生成器
- `vector_store.py`: ChromaDB 向量存储封装

**生成层 (`src/synthesis/`)**:
- `answer.py`: 答案格式化器（引用标注）

**测试 (`tests/`)**:
- `test_tools.py`: 工具层测试
- `test_ingestion.py`: 摄取层测试
- `test_index.py`: 索引层测试
- `test_agent.py`: Agent 层测试

## Key Patterns

**工具定义**: 继承 `Tool` 基类，实现 `name`、`description`、`parameters`、`execute()`

**ReAct 循环** (`orchestrator.py`):
1. 发送问题+工具定义给 LLM
2. LLM 返回 tool_calls 则执行工具，结果加入对话历史
3. 循环直到 LLM 返回最终答案或达到 max_iterations

**CLI 命令**:
- `/help` - 显示帮助
- `/load <路径>` - 加载 PDF 文档
- `/docs` - 查看已加载文档
- `/save [名称]` - 保存会话
- `/history` - 查看对话历史
- `/clear` - 清除历史
- `/exit` - 退出

## Learning Path

**理论学习**: `docs/LEARNING_PATH.md` + `docs/QUIZ.md`

**开发路线图**: `docs/DEVELOPMENT_ROADMAP.md` - 详细开发计划和进度追踪

**实验脚本**: `experiments/` 目录 - 每个步骤的独立实验

## Environment Variables

```
OPENAI_API_KEY=<required>
OPENAI_BASE_URL=<optional, for proxies>
MODEL_NAME=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
CHROMA_PERSIST_DIR=./chroma_db
MAX_ITERATIONS=10
```

## Development Notes

### 阶段 1-2: 基础 Agent
- 实现了 Tool 基类和 ToolRegistry
- 完成 simple_agent（单次调用）和 orchestrator（ReAct循环）
- 使用 mock 数据演示多轮工具调用

### 阶段 3: RAG 集成
- Step 3.1: Embedding 基础 → `src/index/embedder.py`
- Step 3.2: PDF 文档加载 → `src/ingestion/loader.py`
- Step 3.3: 文档切分 Chunking → `src/ingestion/chunker.py`
- Step 3.4: 向量数据库 → `src/index/vector_store.py`
- Step 3.5: 完整摄取流程 → `experiments/05_full_ingestion.py`
- Step 3.6: 检索工具 → `src/tools/retrieval.py`
- Step 3.7: 集成测试 → `experiments/06_rag_agent.py`

### 阶段 4: 完善功能
- Step 4.1: 答案生成优化 → `src/synthesis/answer.py`
- Step 4.2: CLI 交互 → `src/interface/cli.py`, `session.py`
- Step 4.3: 测试用例 → `tests/test_*.py`
