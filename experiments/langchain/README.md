# LangChain 学习实验

通过对比自己实现的代码，学习 LangChain 的核心概念。

## 前置条件

```bash
pip install langchain langchain-openai langchain-chroma langchain-community
```

## 学习顺序

| 文件 | 内容 | 对比点 |
|------|------|--------|
| `01_tool_comparison.py` | Tool 定义 | `Tool` 基类 vs `@tool` / `BaseTool` |
| `02_agent_comparison.py` | Agent 循环 | `AgentOrchestrator` vs `AgentExecutor` |
| `03_rag_comparison.py` | RAG 流程 | 完整流程对比 |

## 运行方式

```bash
# 逐个运行
python experiments/langchain/01_tool_comparison.py
python experiments/langchain/02_agent_comparison.py
python experiments/langchain/03_rag_comparison.py
```

## 核心对应关系

```
我们的实现                    LangChain
──────────────────────────────────────────────────
Tool 基类                  →  BaseTool / @tool
ToolRegistry               →  ToolKit
AgentOrchestrator          →  AgentExecutor
VectorStore                →  Chroma (langchain版)
RetrievalTool              →  create_retriever_tool
DocumentLoader             →  TextLoader / PyPDFLoader
Chunker                    →  RecursiveCharacterTextSplitter
```

## 学习建议

1. **先运行**：不改代码，直接运行看输出
2. **对比源码**：打开我们的实现和 LangChain 源码对比
3. **修改实验**：尝试改参数、换模型、加功能
4. **阅读文档**：遇到不懂的概念查 LangChain 文档
