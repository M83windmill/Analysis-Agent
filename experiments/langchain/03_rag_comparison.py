"""
LangChain 学习 03 - RAG 对比

对比我们的 RAG 实现 vs LangChain 的 RAG

这是最重要的对比！展示完整的 RAG 流程。

运行前先安装：
    pip install langchain langchain-openai langchain-chroma

运行方式：
    python experiments/langchain/03_rag_comparison.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

print("=" * 70)
print("Part 1: 我们的 RAG 实现")
print("=" * 70)

# ========== 我们的实现 ==========
print("""
我们的 RAG 流程:

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  PDF/TXT    │ →  │  Chunker    │ →  │ VectorStore │
│  Loader     │    │  (切分)      │    │  (存储)      │
└─────────────┘    └─────────────┘    └─────────────┘
                                            │
                                            ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Answer    │ ←  │   Agent     │ ←  │  Retrieval  │
│  (输出)      │    │  (决策)      │    │   Tool      │
└─────────────┘    └─────────────┘    └─────────────┘

代码流程:
1. loader.load(pdf_path)         # 加载文档
2. chunker.split(text)           # 切分文本
3. store.add_documents(chunks)   # 存入向量库
4. tool = RetrievalTool(store)   # 创建检索工具
5. agent.register_tool(tool)     # 注册到 Agent
6. agent.run(question)           # 运行
""")

from src.ingestion.loader import DocumentLoader
from src.ingestion.chunker import Chunker
from src.index.vector_store import VectorStore
from src.tools.retrieval import RetrievalTool
from src.agent.orchestrator import AgentOrchestrator

# 准备测试数据
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sample_path = os.path.join(project_root, "data", "sample_report.txt")

print(f"\n加载文档: {sample_path}")
loader = DocumentLoader()
doc = loader.load(sample_path)
print(f"  页数: {doc.page_count}")

print("\n切分文档...")
chunker = Chunker(chunk_size=500, overlap=50)
chunks = []
for page in doc.pages:
    page_chunks = chunker.split(page.text, metadata={"page": page.page_num})
    chunks.extend(page_chunks)
print(f"  块数: {len(chunks)}")

print("\n存入向量库...")
store = VectorStore(collection_name="our_rag_demo", persist_directory=None)
store.add_documents(
    texts=[c.text for c in chunks],
    metadatas=[c.metadata for c in chunks]
)
print(f"  记录数: {store.count}")

print("\n创建 Agent...")
tool = RetrievalTool(vector_store=store, top_k=2)
agent = AgentOrchestrator(model="gpt-4o-mini", max_iterations=3, verbose=False)
agent.register_tool(tool)

print("\n提问: 苹果的总收入是多少？")
answer = agent.run("苹果的总收入是多少？")
print(f"回答: {answer}")


print("\n" + "=" * 70)
print("Part 2: LangChain 的 RAG 实现")
print("=" * 70)

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_chroma import Chroma
    from langchain_community.document_loaders import TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_core.tools import create_retriever_tool
    from langgraph.prebuilt import create_react_agent

    print("""
LangChain 的 RAG 流程:

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ TextLoader  │ →  │TextSplitter │ →  │   Chroma    │
│ (加载)       │    │  (切分)      │    │  (向量库)    │
└─────────────┘    └─────────────┘    └─────────────┘
                                            │
                                            ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Answer    │ ←  │ ReAct Agent │ ←  │ Retriever   │
│  (输出)      │    │ (langgraph) │    │   Tool      │
└─────────────┘    └─────────────┘    └─────────────┘
""")

    # 1. 加载文档
    print(f"\n加载文档: {sample_path}")
    lc_loader = TextLoader(sample_path, encoding='utf-8')
    documents = lc_loader.load()
    print(f"  文档数: {len(documents)}")

    # 2. 切分文档
    print("\n切分文档...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    splits = text_splitter.split_documents(documents)
    print(f"  块数: {len(splits)}")

    # 3. 存入向量库
    print("\n存入向量库...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        collection_name="lc_rag_demo"
    )
    print(f"  完成")

    # 4. 创建 Retriever Tool（一行代码！）
    print("\n创建 Retriever Tool...")
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    retriever_tool = create_retriever_tool(
        retriever,
        name="search_report",
        description="搜索财务报告。用于查询收入、利润等财务数据。"
    )
    print("  create_retriever_tool() - 一行创建检索工具")

    # 5. 创建 Agent（使用 langgraph）
    print("\n创建 Agent...")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = create_react_agent(llm, [retriever_tool])
    print("  create_react_agent() - 一行创建 Agent")

    # 6. 提问
    print("\n提问: 苹果的总收入是多少？")
    result = agent.invoke({"messages": [("user", "苹果的总收入是多少？")]})
    final_message = result["messages"][-1]
    print(f"回答: {final_message.content}")


    print("\n" + "=" * 70)
    print("Part 3: 对比总结")
    print("=" * 70)

    print("""
┌────────────────────┬──────────────────────────────────────────┐
│     我们的实现       │           LangChain 实现                  │
├────────────────────┼──────────────────────────────────────────┤
│ DocumentLoader     │ TextLoader / PyPDFLoader / ...           │
│                    │ (支持更多格式)                             │
├────────────────────┼──────────────────────────────────────────┤
│ Chunker            │ RecursiveCharacterTextSplitter           │
│                    │ (更智能的切分策略)                         │
├────────────────────┼──────────────────────────────────────────┤
│ VectorStore        │ Chroma / FAISS / Pinecone / ...          │
│                    │ (统一接口，支持多种后端)                    │
├────────────────────┼──────────────────────────────────────────┤
│ RetrievalTool      │ create_retriever_tool()                  │
│ (手动实现)          │ (一行代码创建)                            │
├────────────────────┼──────────────────────────────────────────┤
│ 手动拼接流程         │ 可用 LCEL 链式组合                        │
└────────────────────┴──────────────────────────────────────────┘

LangChain 的优势:
1. 更多内置 Loader（PDF、HTML、Notion、Slack...）
2. 更多向量库支持（Pinecone、Weaviate、Milvus...）
3. create_retriever_tool 一行创建检索工具
4. LCEL 可以优雅地组合各组件

我们实现的价值:
1. 理解每个组件的原理
2. 更轻量，无框架依赖
3. 完全可控，易于调试
4. 面试时能讲清楚底层逻辑
""")

except ImportError as e:
    print(f"\n❌ 需要先安装 LangChain:")
    print("   pip install langchain langchain-openai langchain-chroma")
    print(f"\n错误详情: {e}")


print("\n" + "=" * 70)
print("完成！你已经对比了完整的 RAG 流程。")
print("=" * 70)
