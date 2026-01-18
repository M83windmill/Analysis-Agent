"""
向量存储 - Vector Store

封装 ChromaDB 操作，提供简洁的 API。

核心功能：
=========
1. 添加文档（自动生成 Embedding）
2. 语义搜索
3. 元数据过滤
4. 持久化存储

生产环境说明：
=============
ChromaDB 适合学习和小项目。大规模生产环境考虑：
- Pinecone（云托管）
- Milvus/Qdrant（自建）
- pgvector（PostgreSQL扩展）
"""

import os
from dataclasses import dataclass
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()


@dataclass
class SearchResult:
    """
    搜索结果
    
    属性：
        text: 文档内容
        metadata: 元数据
        score: 相似度分数（0-1，越高越相似）
        id: 文档ID
    """
    text: str
    metadata: dict
    score: float
    id: str
    
    def __repr__(self) -> str:
        preview = self.text[:40].replace('\n', ' ')
        return f"SearchResult(score={self.score:.3f}, '{preview}...')"


class VectorStore:
    """
    向量存储
    
    使用方法：
        store = VectorStore(collection_name="my_docs")
        
        # 添加文档
        store.add_documents(
            texts=["文本1", "文本2"],
            metadatas=[{"year": 2023}, {"year": 2022}]
        )
        
        # 搜索
        results = store.search("查询", top_k=3)
        
        # 带过滤的搜索
        results = store.search("查询", where={"year": 2023})
    """
    
    def __init__(
        self,
        collection_name: str = "documents",
        persist_directory: str = None,
        embedding_model: str = None
    ):
        """
        初始化向量存储
        
        参数：
            collection_name: 集合名称
            persist_directory: 持久化目录，None 则使用内存存储
            embedding_model: Embedding 模型名称
        """
        self.collection_name = collection_name
        
        # 创建 Embedding 函数
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name=embedding_model or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        )
        
        # 创建客户端
        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.Client()
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
    
    def add_documents(
        self,
        texts: list[str],
        metadatas: list[dict] = None,
        ids: list[str] = None
    ) -> list[str]:
        """
        添加文档
        
        参数：
            texts: 文本列表
            metadatas: 元数据列表（可选）
            ids: 文档ID列表（可选，自动生成）
            
        返回：
            文档ID列表
        """
        # 自动生成 ID
        if ids is None:
            existing_count = self.collection.count()
            ids = [f"doc_{existing_count + i}" for i in range(len(texts))]
        
        # 确保 metadatas 有值
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        # 添加到集合
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        return ids
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        where: dict = None,
        min_score: float = 0.0
    ) -> list[SearchResult]:
        """
        语义搜索
        
        参数：
            query: 查询文本
            top_k: 返回结果数量
            where: 元数据过滤条件
            min_score: 最低相似度阈值
            
        返回：
            SearchResult 列表
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where
        )
        
        # 转换为 SearchResult
        search_results = []
        
        if results['documents'] and results['documents'][0]:
            for i, (doc, meta, distance, doc_id) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0],
                results['ids'][0]
            )):
                # ChromaDB 返回距离，转换为相似度
                score = 1 - distance
                
                if score >= min_score:
                    search_results.append(SearchResult(
                        text=doc,
                        metadata=meta,
                        score=score,
                        id=doc_id
                    ))
        
        return search_results
    
    def delete(self, ids: list[str]) -> None:
        """删除指定文档"""
        self.collection.delete(ids=ids)
    
    def clear(self) -> None:
        """清空集合"""
        # ChromaDB 没有直接清空的方法，需要删除重建
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function
        )
    
    @property
    def count(self) -> int:
        """文档数量"""
        return self.collection.count()
    
    def __repr__(self) -> str:
        return f"VectorStore(collection='{self.collection_name}', count={self.count})"


# ========== 便捷函数 ==========

def create_vector_store(
    collection_name: str = "documents",
    persist: bool = False
) -> VectorStore:
    """
    快速创建向量存储
    
    参数：
        collection_name: 集合名称
        persist: 是否持久化
    """
    persist_dir = "./chroma_db" if persist else None
    return VectorStore(
        collection_name=collection_name,
        persist_directory=persist_dir
    )


# ========== 测试代码 ==========

if __name__ == "__main__":
    """
    运行测试：python -m src.index.vector_store
    """
    
    print("=" * 60)
    print("VectorStore 模块测试")
    print("=" * 60)
    
    # 创建存储
    store = VectorStore(collection_name="test_collection")
    print(f"\n创建: {store}")
    
    # 添加文档
    print("\n【测试 1】添加文档")
    print("-" * 40)
    
    texts = [
        "2023财年毛利率为44.1%",
        "2022财年毛利率为43.3%",
        "iPhone收入200,583百万美元",
    ]
    metadatas = [
        {"year": 2023, "topic": "毛利率"},
        {"year": 2022, "topic": "毛利率"},
        {"year": 2023, "topic": "iPhone"},
    ]
    
    ids = store.add_documents(texts, metadatas)
    print(f"添加 {len(ids)} 个文档: {ids}")
    print(f"当前数量: {store.count}")
    
    # 搜索
    print("\n【测试 2】语义搜索")
    print("-" * 40)
    
    results = store.search("苹果的毛利率", top_k=2)
    print(f"查询: '苹果的毛利率'")
    for r in results:
        print(f"  {r}")
    
    # 带过滤的搜索
    print("\n【测试 3】带过滤的搜索")
    print("-" * 40)
    
    results = store.search("收入", where={"year": 2023})
    print(f"查询: '收入', 过滤: year=2023")
    for r in results:
        print(f"  {r}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

