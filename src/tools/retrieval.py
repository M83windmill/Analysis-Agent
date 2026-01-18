"""
检索工具 - Retrieval Tool

这是 RAG Agent 的核心工具！

作用：
=====
让 Agent 能够从向量数据库中检索相关文档。
当用户问"苹果的收入是多少"时，Agent 会调用这个工具
从财报中找到相关段落，然后基于这些段落回答问题。

与 MockSearchTool 的区别：
=======================
- MockSearchTool: 硬编码的假数据，用于演示
- RetrievalTool: 真正的语义检索，连接向量数据库

设计要点：
========
1. 依赖注入：接收 VectorStore 实例，而不是自己创建
2. 格式化输出：返回结果包含来源信息（页码），方便 LLM 引用
3. 可选过滤：支持按元数据过滤（如年份）
"""

from typing import Optional
from .base import Tool
from src.index.vector_store import VectorStore


class RetrievalTool(Tool):
    """
    语义检索工具
    
    使用向量数据库进行语义搜索，返回与查询最相关的文档片段。
    
    使用方法：
        # 1. 先准备好向量存储（已经摄取了文档）
        store = VectorStore(collection_name="financial_reports")
        store.add_documents(texts, metadatas)
        
        # 2. 创建检索工具
        retrieval_tool = RetrievalTool(vector_store=store)
        
        # 3. 注册到 Agent
        agent.register_tool(retrieval_tool)
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        top_k: int = 3,
        min_score: float = 0.0
    ):
        """
        初始化检索工具
        
        参数：
            vector_store: 向量存储实例（已经摄取了文档）
            top_k: 每次检索返回的结果数量
            min_score: 最低相似度阈值，低于此值的结果会被过滤
        """
        self.store = vector_store
        self.top_k = top_k
        self.min_score = min_score
    
    @property
    def name(self) -> str:
        """工具名称"""
        return "search_report"
    
    @property
    def description(self) -> str:
        """
        工具描述 - 这决定了 LLM 何时调用这个工具
        
        描述要清晰说明：
        1. 这个工具能做什么
        2. 什么时候应该用它
        3. 能查询什么类型的信息
        """
        return (
            "在财务报告中搜索信息。"
            "当需要查询公司财务数据时使用，如：收入、利润、资产、负债、现金流等。"
            "输入搜索关键词，返回相关的财务数据和来源页码。"
            "如果需要特定年份的数据，可以指定 year 参数。"
        )
    
    @property
    def parameters(self) -> dict:
        """参数定义 - JSON Schema 格式"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "搜索关键词或问题。"
                        "例如：'总收入'、'毛利率'、'现金流'、'资产负债'。"
                        "支持中英文，会自动进行语义匹配。"
                    )
                },
                "year": {
                    "type": "integer",
                    "description": (
                        "可选。指定财年年份，如 2023、2024。"
                        "如果不指定，将搜索所有年份的数据。"
                    )
                }
            },
            "required": ["query"]
        }
    
    def execute(self, query: str, year: int = None) -> str:
        """
        执行检索
        
        参数：
            query: 搜索查询
            year: 可选的年份过滤（如果元数据中有 year 字段）
        
        返回：
            格式化的检索结果，包含内容和来源
        """
        # 构建元数据过滤条件
        where = None
        if year is not None:
            where = {"year": year}
        
        # 执行检索
        results = self.store.search(
            query=query,
            top_k=self.top_k,
            where=where,
            min_score=self.min_score
        )
        
        # 如果带年份过滤没有结果，尝试不过滤
        if not results and year is not None:
            results = self.store.search(
                query=query,
                top_k=self.top_k,
                where=None,
                min_score=self.min_score
            )
            if results:
                # 在结果中注明没有严格按年份过滤
                pass  # 继续处理，下面会返回结果
        
        # 格式化输出
        if not results:
            return f"未找到关于 '{query}' 的相关信息。请尝试使用不同的关键词。"
        
        # 构建返回文本
        output_parts = []
        output_parts.append(f"找到 {len(results)} 条相关信息：\n")
        
        for i, result in enumerate(results, 1):
            # 获取来源信息
            page = result.metadata.get("page", "未知")
            source = result.metadata.get("source", "")
            score = result.score
            
            # 格式化单条结果
            output_parts.append(f"[{i}] 来源: 第{page}页")
            if source:
                output_parts.append(f"    文件: {source}")
            output_parts.append(f"    相似度: {score:.2f}")
            output_parts.append(f"    内容: {result.text[:500]}...")  # 限制长度
            output_parts.append("")
        
        return "\n".join(output_parts)


# ========== 便捷函数 ==========

def create_retrieval_tool(
    vector_store: VectorStore,
    top_k: int = 3
) -> RetrievalTool:
    """
    快速创建检索工具
    
    参数：
        vector_store: 向量存储实例
        top_k: 返回结果数量
    """
    return RetrievalTool(vector_store=vector_store, top_k=top_k)


# ========== 测试代码 ==========

if __name__ == "__main__":
    """
    运行测试：python -m src.tools.retrieval
    
    注意：需要先运行数据摄取，确保向量数据库中有数据
    """
    import os
    import sys
    import json
    
    # 添加项目根目录
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    from dotenv import load_dotenv
    load_dotenv()
    
    from src.ingestion.loader import DocumentLoader
    from src.ingestion.chunker import Chunker
    from src.index.vector_store import VectorStore
    
    print("=" * 60)
    print("RetrievalTool 模块测试")
    print("=" * 60)
    
    # 1. 准备数据 - 加载并切分文档
    print("\n[步骤 1] 准备数据...")
    
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pdf_path = os.path.join(project_root, "data", "FY25_Q4_Consolidated_Financial_Statements.pdf")
    
    if not os.path.exists(pdf_path):
        pdf_path = os.path.join(project_root, "data", "sample_report.txt")
    
    loader = DocumentLoader()
    document = loader.load(pdf_path)
    print(f"  加载文档: {document.page_count} 页")
    
    chunker = Chunker(chunk_size=800, overlap=100)
    all_chunks = []
    for page in document.pages:
        chunks = chunker.split(page.text, metadata={
            "source": os.path.basename(document.source),
            "page": page.page_num
        })
        all_chunks.extend(chunks)
    print(f"  切分成 {len(all_chunks)} 块")
    
    # 2. 存入向量数据库
    print("\n[步骤 2] 存入向量数据库...")
    store = VectorStore(collection_name="test_retrieval")
    
    texts = [chunk.text for chunk in all_chunks]
    metadatas = [chunk.metadata for chunk in all_chunks]
    store.add_documents(texts=texts, metadatas=metadatas)
    print(f"  存储完成，共 {store.count} 条记录")
    
    # 3. 创建检索工具
    print("\n[步骤 3] 创建检索工具...")
    tool = RetrievalTool(vector_store=store, top_k=3)
    
    print(f"  工具名称: {tool.name}")
    print(f"  工具描述: {tool.description[:50]}...")
    
    # 4. 查看 OpenAI 格式
    print("\n[步骤 4] OpenAI 工具格式:")
    print(json.dumps(tool.to_openai_tool(), indent=2, ensure_ascii=False))
    
    # 5. 测试检索
    print("\n[步骤 5] 测试检索...")
    
    test_queries = [
        ("total revenue", None),
        ("gross margin", None),
        ("cash flow", None),
    ]
    
    for query, year in test_queries:
        print(f"\n{'-' * 50}")
        print(f"查询: '{query}'" + (f", 年份: {year}" if year else ""))
        print(f"{'-' * 50}")
        
        result = tool.execute(query=query, year=year)
        # 只显示前 500 字符
        print(result[:500] + "..." if len(result) > 500 else result)
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

