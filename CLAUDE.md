# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

财报分析助手 Agent - 一个学习型项目，既是真实可用的 Agent，也是学习 Agent 架构的教学项目。

**当前进度**:
- [x] 阶段1-2: 基础 Agent 实现（Tool Use + ReAct 循环）
- [~] 阶段3: RAG 集成（进行中，已完成 Step 3.1-3.4）
- [ ] 阶段4: 完善功能（CLI、答案生成、测试）

## Development Commands

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 设置 OPENAI_API_KEY

# 运行模块测试
python -m src.agent.simple_agent      # 单次工具调用 Agent
python -m src.agent.orchestrator      # ReAct 循环 Agent
python -m src.tools.base              # 工具注册表测试
python -m src.tools.calculator        # 计算器工具测试
```

## Architecture

```
用户输入 → Agent决策层(ReAct循环) → 工具层 → 输出
                  ↓↑
           知识索引层 ← 文档摄取层
```

### 已实现

**Agent 层 (`src/agent/`)**:
- `simple_agent.py`: 单次工具调用，理解 Tool Use 的起点
- `orchestrator.py`: 完整 ReAct 循环，支持多轮工具调用

**工具层 (`src/tools/`)**:
- `base.py`: `Tool` 抽象基类 + `ToolRegistry` 工具注册表
- `calculator.py`: 数学表达式计算工具

### 待实现 (阶段3-4)

- `src/ingestion/`: PDF加载、文本切分、元数据标注
- `src/index/`: Embedding生成、ChromaDB向量存储、检索策略
- `src/synthesis/`: 证据汇总、答案生成
- `src/interface/`: CLI交互、会话管理

## Key Patterns

**工具定义**: 继承 `Tool` 基类，实现 `name`、`description`、`parameters`、`execute()`

**ReAct 循环** (`orchestrator.py:157`):
1. 发送问题+工具定义给 LLM
2. LLM 返回 tool_calls 则执行工具，结果加入对话历史
3. 循环直到 LLM 返回最终答案或达到 max_iterations

## Learning Path

**理论学习**: `docs/LEARNING_PATH.md` + `docs/QUIZ.md`

**开发路线图**: `docs/DEVELOPMENT_ROADMAP.md` - 详细开发计划和进度追踪

**实验脚本**: `experiments/` 目录 - 每个步骤的独立实验

## Environment Variables

```
OPENAI_API_KEY=<required>
OPENAI_BASE_URL=<optional, for proxies>
MODEL_NAME=gpt-4
EMBEDDING_MODEL=text-embedding-3-small
CHROMA_PERSIST_DIR=./chroma_db
MAX_ITERATIONS=10
```

## Development Notes

_记录开发过程中的关键点和决策_

### 阶段 1-2 完成: 基础 Agent
- 实现了 Tool 基类和 ToolRegistry
- 完成 simple_agent（单次调用）和 orchestrator（ReAct循环）
- 使用 mock 数据演示多轮工具调用

### 当前进度: 阶段 3 - RAG 集成
- ✅ Step 3.1: Embedding 基础 - 完成
- ✅ Step 3.2: PDF 文档加载 - 完成
- ✅ Step 3.3: 文档切分 Chunking - 完成
- ✅ Step 3.4: 向量数据库入门 - 完成
- 🚧 Step 3.5: 完整摄取流程 - 进行中
- 详细进度见 `docs/DEVELOPMENT_ROADMAP.md`

### 已创建的模块
- `src/index/embedder.py` - Embedding 生成器
- `src/ingestion/loader.py` - 文档加载器
- `src/ingestion/chunker.py` - 文档切分器
- `src/index/vector_store.py` - 向量存储封装
