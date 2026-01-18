"""
向量数据库实验 - ChromaDB

目标：掌握 ChromaDB 的基本操作

运行方式：python experiments/04_vector_store.py

为什么需要向量数据库？
====================
1. Embedding 生成后要存到某个地方
2. 用户查询时要快速找到最相似的向量
3. 普通数据库不擅长"相似度搜索"
4. 向量数据库专门优化了这类查询

ChromaDB 简介：
==============
- 轻量级，可以本地运行（不需要服务器）
- 支持持久化（数据不会丢失）
- API 简单易用
- 适合学习和小型项目
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import chromadb
from chromadb.utils import embedding_functions

# 使用 OpenAI 的 Embedding
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)


def main():
    """主实验流程"""
    
    print("=" * 70)
    print("实验 4: 向量数据库 (ChromaDB)")
    print("=" * 70)
    
    # ========== 实验 4.1: 创建客户端和集合 ==========
    print("\n" + "=" * 70)
    print("[实验 4.1] 创建 ChromaDB 客户端和集合")
    print("=" * 70)
    
    # 创建内存客户端（数据不持久化，重启后消失）
    # 如果要持久化，用: chromadb.PersistentClient(path="./chroma_db")
    client = chromadb.Client()
    
    # 创建或获取集合（类似数据库中的"表"）
    # 集合名称必须唯一
    collection = client.get_or_create_collection(
        name="financial_reports",
        embedding_function=openai_ef,  # 自动生成 Embedding
        metadata={"description": "苹果财报数据"}
    )
    
    print(f"集合名称: {collection.name}")
    print(f"当前文档数: {collection.count()}")
    
    # ========== 实验 4.2: 添加文档 ==========
    print("\n" + "=" * 70)
    print("[实验 4.2] 添加文档到集合")
    print("=" * 70)
    
    # 准备测试数据
    documents = [
        "2023财年毛利率为44.1%，毛利润为169,148百万美元",
        "2022财年毛利率为43.3%，毛利润为170,782百万美元",
        "2023财年总收入383,285百万美元，同比下降2.8%",
        "2022财年总收入394,328百万美元",
        "iPhone收入200,583百万美元，占总收入52.3%",
        "服务收入85,200百万美元，同比增长9.1%",
        "大中华区收入72,559百万美元，占比18.9%",
        "研发费用29,915百万美元，占收入7.8%",
    ]
    
    # 元数据（每个文档的附加信息）
    metadatas = [
        {"year": 2023, "topic": "毛利率", "page": 1},
        {"year": 2022, "topic": "毛利率", "page": 1},
        {"year": 2023, "topic": "收入", "page": 1},
        {"year": 2022, "topic": "收入", "page": 1},
        {"year": 2023, "topic": "iPhone", "page": 2},
        {"year": 2023, "topic": "服务", "page": 2},
        {"year": 2023, "topic": "地区", "page": 3},
        {"year": 2023, "topic": "研发", "page": 3},
    ]
    
    # 文档ID（必须唯一）
    ids = [f"doc_{i}" for i in range(len(documents))]
    
    # 添加到集合
    # ChromaDB 会自动调用 embedding_function 生成向量
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    print(f"已添加 {len(documents)} 个文档")
    print(f"当前文档数: {collection.count()}")
    
    print("\n添加的文档:")
    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        print(f"  [{i}] {meta} -> {doc[:40]}...")
    
    # ========== 实验 4.3: 基础查询 ==========
    print("\n" + "=" * 70)
    print("[实验 4.3] 基础查询 - 语义搜索")
    print("=" * 70)
    
    query = "苹果公司的毛利率是多少"
    print(f"\n查询: '{query}'")
    
    results = collection.query(
        query_texts=[query],
        n_results=3  # 返回最相似的3个
    )
    
    print(f"\nTop 3 结果:")
    for i, (doc, meta, distance) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        # ChromaDB 返回的是距离，越小越相似
        similarity = 1 - distance  # 转换为相似度
        print(f"  [{i+1}] 相似度: {similarity:.4f}")
        print(f"      元数据: {meta}")
        print(f"      内容: {doc}")
    
    # ========== 实验 4.4: 带元数据过滤的查询 ==========
    print("\n" + "=" * 70)
    print("[实验 4.4] 带元数据过滤的查询")
    print("=" * 70)
    
    query = "收入是多少"
    print(f"\n查询: '{query}'")
    print("过滤条件: year = 2023")
    
    results_filtered = collection.query(
        query_texts=[query],
        n_results=3,
        where={"year": 2023}  # 只搜索2023年的数据
    )
    
    print(f"\n只看2023年的结果:")
    for i, (doc, meta) in enumerate(zip(
        results_filtered['documents'][0],
        results_filtered['metadatas'][0]
    )):
        print(f"  [{i+1}] {meta['topic']}: {doc[:50]}...")
    
    # 对比：不过滤
    print(f"\n不过滤的结果（包含2022年）:")
    results_all = collection.query(
        query_texts=[query],
        n_results=3
    )
    for i, (doc, meta) in enumerate(zip(
        results_all['documents'][0],
        results_all['metadatas'][0]
    )):
        print(f"  [{i+1}] {meta['year']}年: {doc[:50]}...")
    
    # ========== 实验 4.5: 复杂过滤条件 ==========
    print("\n" + "=" * 70)
    print("[实验 4.5] 复杂过滤条件")
    print("=" * 70)
    
    query = "财务数据"
    print(f"\n查询: '{query}'")
    print("过滤条件: year = 2023 AND (topic = '毛利率' OR topic = '收入')")
    
    results_complex = collection.query(
        query_texts=[query],
        n_results=5,
        where={
            "$and": [
                {"year": 2023},
                {"$or": [
                    {"topic": "毛利率"},
                    {"topic": "收入"}
                ]}
            ]
        }
    )
    
    print(f"\n过滤后结果:")
    for i, (doc, meta) in enumerate(zip(
        results_complex['documents'][0],
        results_complex['metadatas'][0]
    )):
        print(f"  [{i+1}] {meta}: {doc[:40]}...")
    
    # ========== 实验 4.6: 持久化演示 ==========
    print("\n" + "=" * 70)
    print("[实验 4.6] 持久化存储")
    print("=" * 70)
    
    # 创建持久化客户端
    persist_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "chroma_db"
    )
    
    print(f"持久化路径: {persist_path}")
    print("""
持久化代码示例:
    
    # 创建持久化客户端
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # 创建集合并添加数据（同上）
    collection = client.get_or_create_collection("my_data")
    collection.add(documents=[...], ids=[...])
    
    # 下次启动时，数据还在
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection("my_data")
    print(collection.count())  # 数据还在！
""")
    
    # ========== 总结 ==========
    print("\n" + "=" * 70)
    print("实验总结")
    print("=" * 70)
    print("""
ChromaDB 核心概念:

1. Client（客户端）
   - chromadb.Client()           # 内存存储，重启丢失
   - chromadb.PersistentClient() # 持久化存储
   
2. Collection（集合）
   - 类似数据库的"表"
   - 一个集合存储一类文档
   - 指定 embedding_function 自动生成向量

3. 添加文档
   collection.add(
       documents=[...],  # 文本内容
       metadatas=[...],  # 元数据（年份、页码等）
       ids=[...]         # 唯一ID
   )

4. 查询
   collection.query(
       query_texts=["问题"],     # 查询文本
       n_results=3,              # 返回数量
       where={"year": 2023}      # 元数据过滤
   )

关键理解:
- ChromaDB 自动处理 Embedding，我们只需要传文本
- 元数据过滤可以缩小搜索范围，提高精准度
- 返回的是"距离"，越小越相似（可转换为相似度）
""")


if __name__ == "__main__":
    main()

