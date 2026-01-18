"""
RAG Agent 实验 - 完整的财报问答系统

目标：把 RAG 接入 Agent，实现真正的财报问答

运行方式：python experiments/06_rag_agent.py

完整流程：
=========

阶段1：数据摄取（一次性）
    PDF 文件
        |
        v DocumentLoader
    Document 对象
        |
        v Chunker
    Chunk 列表
        |
        v VectorStore
    向量数据库（持久化）

阶段2：问答运行（每次查询）
    用户问题
        |
        v AgentOrchestrator
    ReAct 循环开始
        |
        v LLM 决策
    调用 RetrievalTool
        |
        v VectorStore.search()
    返回相关文档
        |
        v LLM 生成答案
    带引用的回答

这个实验将帮助你理解：
==================
1. RAG 如何与 Agent 的 ReAct 循环结合
2. 真实的语义检索 vs 之前的模拟数据
3. Agent 如何利用检索结果生成带引用的答案
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# 导入我们的模块
from src.ingestion.loader import DocumentLoader
from src.ingestion.chunker import Chunker
from src.index.vector_store import VectorStore
from src.tools.retrieval import RetrievalTool
from src.tools.calculator import CalculatorTool
from src.agent.orchestrator import AgentOrchestrator


def ingest_documents(pdf_path: str, collection_name: str = "financial_reports") -> VectorStore:
    """
    数据摄取：PDF -> 加载 -> 切分 -> 存储
    
    参数：
        pdf_path: PDF 文件路径
        collection_name: 向量数据库集合名称
    
    返回：
        VectorStore 实例（已经存入数据）
    """
    print("\n" + "=" * 70)
    print("[数据摄取] 加载和处理文档...")
    print("=" * 70)
    
    # 1. 加载文档
    print("\n[步骤 1] 加载文档...")
    loader = DocumentLoader()
    document = loader.load(pdf_path)
    print(f"  来源: {os.path.basename(document.source)}")
    print(f"  页数: {document.page_count}")
    print(f"  总字符数: {document.total_chars:,}")
    
    # 2. 切分文档
    print("\n[步骤 2] 切分文档...")
    chunker = Chunker(chunk_size=800, overlap=100, min_chunk_size=100)
    
    all_chunks = []
    for page in document.pages:
        page_metadata = {
            "source": os.path.basename(document.source),
            "page": page.page_num,
            "title": document.metadata.get("title", "")
        }
        chunks = chunker.split(page.text, metadata=page_metadata)
        all_chunks.extend(chunks)
    
    print(f"  切分块数: {len(all_chunks)}")
    print(f"  平均块大小: {sum(c.char_count for c in all_chunks) // len(all_chunks)} 字符")
    
    # 3. 存入向量数据库
    print("\n[步骤 3] 存入向量数据库...")
    store = VectorStore(
        collection_name=collection_name,
        persist_directory=None  # 内存存储
    )
    
    texts = [chunk.text for chunk in all_chunks]
    metadatas = [chunk.metadata for chunk in all_chunks]
    
    store.add_documents(texts=texts, metadatas=metadatas)
    print(f"  集合名称: {store.collection_name}")
    print(f"  文档数量: {store.count}")
    
    print("\n[摄取完成]")
    
    return store


def create_rag_agent(vector_store: VectorStore) -> AgentOrchestrator:
    """
    创建 RAG Agent
    
    参数：
        vector_store: 向量存储实例
    
    返回：
        配置好的 AgentOrchestrator
    """
    print("\n" + "=" * 70)
    print("[Agent 配置] 创建 RAG Agent...")
    print("=" * 70)
    
    # 创建编排器
    agent = AgentOrchestrator(
        model="gpt-4o-mini",
        max_iterations=10,
        verbose=True
    )
    
    # 注册检索工具（核心！）
    retrieval_tool = RetrievalTool(
        vector_store=vector_store,
        top_k=3,
        min_score=0.0
    )
    agent.register_tool(retrieval_tool)
    
    # 注册计算器工具（用于数值计算）
    calculator_tool = CalculatorTool()
    agent.register_tool(calculator_tool)
    
    print(f"\n已注册工具: {agent.registry.list_tools()}")
    print("[Agent 就绪]")
    
    return agent


def main():
    """主实验流程"""
    
    print("=" * 70)
    print("实验 6: RAG Agent - 财报问答系统")
    print("=" * 70)
    print("""
    本实验演示完整的 RAG + Agent 流程：
    
    1. 将 PDF 文档摄取到向量数据库
    2. 创建配备 RetrievalTool 和 CalculatorTool 的 Agent
    3. 提问并观察 ReAct 循环的运行
    
    Agent 会：
    - 在文档中搜索相关信息
    - 需要时进行数值计算
    - 生成带来源引用的答案
    """)
    
    # 检查 API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n[错误] 请在 .env 文件中设置 OPENAI_API_KEY")
        return
    
    # ========== 阶段1：数据摄取 ==========
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_path = os.path.join(project_root, "data", "FY25_Q4_Consolidated_Financial_Statements.pdf")
    
    if not os.path.exists(pdf_path):
        pdf_path = os.path.join(project_root, "data", "sample_report.txt")
        print(f"\n[提示] PDF 文件不存在，使用: {os.path.basename(pdf_path)}")
    
    vector_store = ingest_documents(pdf_path)
    
    # ========== 阶段2：创建 Agent ==========
    agent = create_rag_agent(vector_store)
    
    # ========== 阶段3：问答测试 ==========
    print("\n" + "=" * 70)
    print("[问答测试] 用真实问题测试 RAG Agent")
    print("=" * 70)
    
    # 测试问题
    test_questions = [
        # 问题1：简单检索
        "苹果公司2025财年的总净销售额是多少？",
        
        # 问题2：需要检索多个数据点
        # "总资产和总负债分别是多少？",
        
        # 问题3：需要检索 + 计算
        # "根据净销售额和销售成本，计算毛利率是多少？",
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n\n{'#' * 70}")
        print(f"# 测试 {i}")
        print(f"{'#' * 70}")
        
        answer = agent.run(question)
        
        print(f"\n{'=' * 70}")
        print("[总结]")
        print(f"问题: {question}")
        print(f"答案: {answer[:500]}..." if len(answer) > 500 else f"答案: {answer}")
        print(f"{'=' * 70}")
    
    # ========== 实验总结 ==========
    print("\n" + "=" * 70)
    print("实验总结")
    print("=" * 70)
    print("""
    关键观察：
    
    1. RAG 集成
       - RetrievalTool 连接 Agent 和 VectorStore
       - 语义搜索找到相关文档片段
       - 结果包含页码，方便引用
    
    2. ReAct 循环
       - Agent 自己决定什么时候搜索、什么时候回答
       - 可以组合多个工具调用（搜索 + 计算）
       - 信息足够时自动停止
    
    3. 真实数据 vs 模拟数据
       - 之前: MockSearchTool 使用硬编码数据
       - 现在: RetrievalTool 使用真实语义搜索
       - 结果取决于实际文档内容
    
    下一步：
    - 添加更多文档到知识库
    - 实现混合搜索（关键词 + 语义）
    - 添加答案验证和事实检查
    """)


if __name__ == "__main__":
    main()
