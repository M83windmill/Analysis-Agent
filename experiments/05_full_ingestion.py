"""
完整摄取流程实验 - Full Ingestion Pipeline

目标：串联所有模块，完成完整的 RAG 数据摄取和检索流程

运行方式：python experiments/05_full_ingestion.py

完整流程：
=========
  PDF 文档
      ↓
  1. 加载 (Loader)
      ↓
  2. 切分 (Chunker)
      ↓
  3. Embedding (自动)
      ↓
  4. 存储 (VectorStore)
      ↓
  5. 检索 (Search)
      ↓
  相关文档片段

这个实验将帮助你理解：
==================
1. 各个模块如何协作
2. 元数据如何贯穿整个流程
3. 从原始 PDF 到检索结果的完整路径
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# 导入我们的模块
from src.ingestion.loader import DocumentLoader, Document
from src.ingestion.chunker import Chunker, Chunk
from src.index.vector_store import VectorStore, SearchResult


def main():
    """主实验流程"""
    
    print("=" * 70)
    print("实验 5: 完整摄取流程 (Full Ingestion Pipeline)")
    print("=" * 70)
    print("""
    本实验将演示完整的 RAG 数据流：
    
    PDF 文件 → 加载 → 切分 → Embedding → 存储 → 检索
    
    使用的模块：
    - src/ingestion/loader.py    (文档加载)
    - src/ingestion/chunker.py   (文档切分)
    - src/index/vector_store.py  (向量存储，内含自动Embedding)
    """)
    
    # ========== 准备工作 ==========
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 使用真实的 PDF 财报
    pdf_path = os.path.join(project_root, "data", "FY25_Q4_Consolidated_Financial_Statements.pdf")
    
    # 如果 PDF 不存在，使用文本文件作为备选
    if not os.path.exists(pdf_path):
        pdf_path = os.path.join(project_root, "data", "sample_report.txt")
        print(f"\n[备选] PDF 文件不存在，使用: {os.path.basename(pdf_path)}")
    else:
        print(f"\n[输入] 财报文件: {os.path.basename(pdf_path)}")
    
    # ========== 步骤 1: 加载文档 ==========
    print("\n" + "=" * 70)
    print("[步骤 1] 加载文档 (Document Loading)")
    print("=" * 70)
    
    loader = DocumentLoader()
    document = loader.load(pdf_path)
    
    print(f"""
    加载完成！
    
    文档信息：
    - 来源: {os.path.basename(document.source)}
    - 页数: {document.page_count}
    - 总字符数: {document.total_chars:,}
    - 元数据: {document.metadata}
    """)
    
    # 显示前几页预览
    print("    页面预览（前3页）:")
    for page in document.pages[:3]:
        preview = page.text[:100].replace('\n', ' ')
        print(f"      第{page.page_num}页: {preview}...")
    
    # ========== 步骤 2: 切分文档 ==========
    print("\n" + "=" * 70)
    print("[步骤 2] 切分文档 (Document Chunking)")
    print("=" * 70)
    
    # 创建切分器
    chunker = Chunker(
        chunk_size=800,    # 每块约800字符
        overlap=100,       # 100字符重叠
        min_chunk_size=100 # 最小块100字符
    )
    
    # 对每一页进行切分，保留页码信息
    all_chunks = []
    
    for page in document.pages:
        # 切分这一页，并附加页码元数据
        page_metadata = {
            "source": os.path.basename(document.source),
            "page": page.page_num,
            "title": document.metadata.get("title", "")
        }
        
        chunks = chunker.split(page.text, metadata=page_metadata)
        all_chunks.extend(chunks)
    
    print(f"""
    切分完成！
    
    切分参数：
    - chunk_size: 800 字符
    - overlap: 100 字符
    - 策略: 按段落边界
    
    切分结果：
    - 原始页数: {document.page_count}
    - 切分后块数: {len(all_chunks)}
    - 平均每页产生: {len(all_chunks) / document.page_count:.1f} 块
    """)
    
    # 显示部分切分结果
    print("    块预览（前5块）:")
    for chunk in all_chunks[:5]:
        preview = chunk.text[:60].replace('\n', ' ')
        print(f"      块 {chunk.index} (第{chunk.metadata.get('page', '?')}页, {chunk.char_count}字符): {preview}...")
    
    # ========== 步骤 3 & 4: Embedding + 存储 ==========
    print("\n" + "=" * 70)
    print("[步骤 3 & 4] Embedding + 存储 (VectorStore 自动处理)")
    print("=" * 70)
    
    print("""
    ChromaDB 的妙处：
    - 我们只需要传入文本，它自动调用 Embedding API
    - 向量和原文都存储在一起，查询时可以直接返回文本
    
    正在创建向量存储并添加文档...
    """)
    
    # 创建向量存储
    store = VectorStore(
        collection_name="financial_report",
        persist_directory=None  # 内存存储，重启后消失
    )
    
    # 准备数据
    texts = [chunk.text for chunk in all_chunks]
    metadatas = [chunk.metadata for chunk in all_chunks]
    
    # 添加到向量存储（这一步会自动调用 Embedding API）
    print(f"    正在对 {len(texts)} 个文本块生成 Embedding 并存储...")
    ids = store.add_documents(texts=texts, metadatas=metadatas)
    
    print(f"""
    存储完成！
    
    向量存储状态：
    - 集合名称: {store.collection_name}
    - 文档数量: {store.count}
    - 生成的ID: {ids[:3]}... (共{len(ids)}个)
    """)
    
    # ========== 步骤 5: 检索测试 ==========
    print("\n" + "=" * 70)
    print("[步骤 5] 检索测试 (Semantic Search)")
    print("=" * 70)
    
    # 测试查询列表
    test_queries = [
        "公司的总收入是多少",
        "毛利率 gross margin",
        "现金流量",
        "资产负债表",
    ]
    
    print("""
    现在测试检索效果！
    
    检索流程：
    1. 用户输入查询
    2. 查询文本 → Embedding
    3. 在向量空间中找最近邻
    4. 返回最相似的文档块
    """)
    
    for query in test_queries:
        print(f"\n{'-' * 60}")
        print(f"[Query] \"{query}\"")
        print(f"{'-' * 60}")
        
        results = store.search(query, top_k=3)
        
        if results:
            for i, result in enumerate(results):
                print(f"\n    [{i+1}] 相似度: {result.score:.4f}")
                print(f"        来源: 第{result.metadata.get('page', '?')}页")
                # 显示文本预览（最多150字符）
                preview = result.text[:150].replace('\n', ' ')
                print(f"        内容: {preview}...")
        else:
            print("    未找到相关结果")
    
    # ========== 实验 5.1: 带元数据过滤的检索 ==========
    print("\n" + "=" * 70)
    print("[实验 5.1] 带元数据过滤的检索")
    print("=" * 70)
    
    print("""
    元数据过滤的威力：
    - 先通过元数据缩小搜索范围
    - 再进行语义搜索
    - 效果：更精准、更快速
    """)
    
    # 查找第1页的内容
    query = "财务数据"
    print(f"\n查询: \"{query}\"")
    print(f"过滤条件: page = 1（只看第1页）")
    
    results_filtered = store.search(query, top_k=3, where={"page": 1})
    
    print(f"\n只看第1页的结果:")
    for i, result in enumerate(results_filtered):
        preview = result.text[:100].replace('\n', ' ')
        print(f"    [{i+1}] 相似度: {result.score:.4f}")
        print(f"        {preview}...")
    
    # 对比：不过滤
    print(f"\n不过滤的结果（可能来自任何页面）:")
    results_all = store.search(query, top_k=3)
    for i, result in enumerate(results_all):
        preview = result.text[:100].replace('\n', ' ')
        print(f"    [{i+1}] 第{result.metadata.get('page', '?')}页, 相似度: {result.score:.4f}")
        print(f"        {preview}...")
    
    # ========== 流程总结 ==========
    print("\n" + "=" * 70)
    print("完整流程总结")
    print("=" * 70)
    print(f"""
    数据流转路径:
    
    ┌──────────────────────────────────────────────────────────────┐
    │  1. PDF 文档                                                  │
    │     {os.path.basename(document.source)}
    │     {document.total_chars:,} 字符, {document.page_count} 页
    └─────────────────────────┬────────────────────────────────────┘
                              │
                              ▼ DocumentLoader.load()
    ┌──────────────────────────────────────────────────────────────┐
    │  2. Document 对象                                             │
    │     按页面结构化存储                                           │
    │     保留元数据: 标题、作者、页码                                │
    └─────────────────────────┬────────────────────────────────────┘
                              │
                              ▼ Chunker.split()
    ┌──────────────────────────────────────────────────────────────┐
    │  3. Chunk 列表                                                │
    │     {len(all_chunks)} 个文本块
    │     每块约 800 字符，带页码元数据                               │
    └─────────────────────────┬────────────────────────────────────┘
                              │
                              ▼ VectorStore.add_documents()
    ┌──────────────────────────────────────────────────────────────┐
    │  4. ChromaDB 向量数据库                                       │
    │     {store.count} 个向量 (1536维)
    │     文本 + 向量 + 元数据 一起存储                              │
    └─────────────────────────┬────────────────────────────────────┘
                              │
                              ▼ VectorStore.search()
    ┌──────────────────────────────────────────────────────────────┐
    │  5. 语义检索                                                  │
    │     用户查询 → Embedding → 最近邻搜索 → 返回相关文档           │
    └──────────────────────────────────────────────────────────────┘
    
    
    关键理解:
    ═════════
    
    1. 为什么要切分？
       - LLM 的 context window 有限
       - 整个文档太大，无法一次传给 LLM
       - 切分后可以只传入相关部分，节省成本、提高精准度
    
    2. 元数据的作用？
       - 追溯来源（答案来自哪一页）
       - 过滤搜索（只看某年/某章节）
       - 多文档管理（区分不同财报）
    
    3. 为什么用向量搜索而不是关键词搜索？
       - 语义相似: "收入" 能找到 "营收"、"revenue"
       - 不需要精确匹配
       - 支持自然语言提问
    
    4. 重叠 (overlap) 的作用？
       - 防止关键信息被切断
       - 如果一个块漏掉了，相邻块可能包含
    """)


if __name__ == "__main__":
    main()

