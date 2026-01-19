# 财报分析助手 Agent

一个基于 LLM 的财报分析 Agent，能够自动检索财报内容、提取关键信息、计算财务指标，并生成带引用的分析报告。

## 项目架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户输入                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  A. 接口层 (Interface)                                          │
│  - CLI 命令行界面                                                │
│  - 会话管理 (保存对话历史)                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  D. Agent 决策层 (Orchestration) ★核心                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  ReAct 循环                                              │    │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐          │    │
│  │  │  思考    │───▶│  行动    │───▶│  观察    │──┐       │    │
│  │  │ Thought  │    │  Action  │    │Observation│  │       │    │
│  │  └──────────┘    └──────────┘    └──────────┘  │       │    │
│  │       ▲                                        │       │    │
│  │       └────────────────────────────────────────┘       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
┌───────────────────────┐    ┌───────────────────────┐
│  E. 工具层 (Tools)     │    │  C. 知识索引层        │
│  - 检索工具           │◀───│  - Embedding          │
│  - 表格抽取           │    │  - 向量数据库         │
│  - 计算器             │    │  - 检索策略           │
│  - 引用工具           │    └───────────────────────┘
└───────────────────────┘              ▲
                                       │
                    ┌──────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  B. 文档摄取层 (Ingestion)                                       │
│  - PDF/HTML/TXT 加载                                            │
│  - 文本清洗与切分 (Chunking)                                     │
│  - 元数据标注                                                    │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                        财报文档                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 目录结构

```
Analysis-Agent/
├── README.md                    # 项目说明 (本文件)
├── CLAUDE.md                    # Claude Code 项目指南
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量示例
│
├── docs/                        # 文档
│   ├── LEARNING_PATH.md         # ★学习路径 (从这里开始)
│   ├── QUIZ.md                  # ★自测题 (检验理解)
│   └── DEVELOPMENT_ROADMAP.md   # 开发路线图
│
├── experiments/                 # 实验脚本 (按步骤学习)
│   ├── 01_embedding_basics.py   # Embedding 基础
│   ├── 02_pdf_loading.py        # PDF 加载
│   ├── 03_chunking.py           # 文档切分
│   ├── 04_vector_store.py       # 向量存储
│   ├── 05_full_ingestion.py     # 完整摄取流程
│   └── 06_rag_agent.py          # RAG Agent 完整演示
│
├── src/
│   ├── interface/               # A层: 接口层
│   │   ├── cli.py               # 命令行界面 (REPL)
│   │   └── session.py           # 会话管理
│   │
│   ├── ingestion/               # B层: 文档摄取层
│   │   ├── loader.py            # PDF/TXT 文件加载
│   │   └── chunker.py           # 文档切分
│   │
│   ├── index/                   # C层: 知识索引层
│   │   ├── embedder.py          # Embedding 生成
│   │   └── vector_store.py      # 向量数据库 (ChromaDB)
│   │
│   ├── agent/                   # D层: Agent决策层 ★核心
│   │   ├── simple_agent.py      # 最简Agent (入门)
│   │   └── orchestrator.py      # 完整Agent (ReAct循环)
│   │
│   ├── tools/                   # E层: 工具层
│   │   ├── base.py              # 工具基类 + 注册表
│   │   ├── calculator.py        # 数学计算工具
│   │   └── retrieval.py         # 语义检索工具
│   │
│   └── synthesis/               # F层: 生成层
│       └── answer.py            # 答案格式化 + 引用
│
├── prompts/                     # Prompt 模板
│   └── AAPL_method.txt          # 苹果财报分析方法
│
├── data/                        # 测试数据
│   └── sample_report.txt        # 示例财报
│
└── tests/                       # 测试 (55个测试用例)
    ├── test_tools.py            # 工具层测试
    ├── test_ingestion.py        # 摄取层测试
    ├── test_index.py            # 索引层测试
    └── test_agent.py            # Agent层测试
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 OpenAI API Key

# 3. 运行 CLI（交互式问答）
python -m src.interface.cli

# 4. 运行实验脚本（学习用）
python experiments/06_rag_agent.py

# 5. 运行测试
pytest tests/ -v                    # 运行所有测试
pytest tests/test_tools.py -v       # 仅测试工具层
SKIP_API_TESTS=1 pytest tests/ -v   # 跳过需要 API 的测试
```

### CLI 命令

在 CLI 中可以使用以下命令：

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/load <文件路径>` | 加载 PDF/TXT 文档 |
| `/docs` | 显示已加载的文档 |
| `/save [名称]` | 保存当前会话 |
| `/list` | 列出所有保存的会话 |
| `/restore <名称>` | 恢复会话 |
| `/history` | 显示对话历史 |
| `/clear` | 清空对话历史 |
| `/exit` | 退出程序 |

## 学习指南

如果你是来学习 Agent 架构的，请按顺序阅读：

1. **[docs/LEARNING_PATH.md](docs/LEARNING_PATH.md)** - 学习路径和核心概念
2. **src/tools/base.py** - 理解工具定义
3. **src/agent/simple_agent.py** - 最简单的 Agent 实现
4. **src/agent/orchestrator.py** - 完整的 ReAct 循环

## 核心概念

### 什么是 Agent?

```
Agent = LLM + 工具 + 循环决策

普通Chatbot: 用户提问 → LLM回答
Agent:       用户提问 → LLM思考 → 调用工具 → 观察结果 → 继续思考... → 最终回答
```

### 为什么需要 Agent?

1. **能力扩展**: LLM 只会"说"，Agent 能"做"（检索、计算、调用API）
2. **知识增强**: 通过 RAG 访问最新/私有数据
3. **多步推理**: 复杂问题分解为多个步骤执行

## 技术栈

| 组件 | 选择 | 说明 |
|-----|------|------|
| LLM | OpenAI GPT-4 | 主力模型 |
| 向量库 | ChromaDB | 轻量级，本地运行 |
| Embedding | text-embedding-3-small | OpenAI 嵌入模型 |
| PDF处理 | PyMuPDF | 快速稳定 |

## License

MIT
