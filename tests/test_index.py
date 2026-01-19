"""
索引层测试 - Index Tests

测试内容：
1. VectorStore - 向量存储（需要 ChromaDB）

运行方式：
    pytest tests/test_index.py -v

注意：
    这些测试需要 OpenAI API Key 来生成 embeddings
    设置环境变量 SKIP_API_TESTS=1 可跳过需要 API 的测试
"""

import pytest
import os

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# 检查是否跳过 API 测试
SKIP_API_TESTS = os.getenv("SKIP_API_TESTS", "0") == "1"
SKIP_REASON = "SKIP_API_TESTS=1 or no API key"

# 检查是否有 API key
HAS_API_KEY = bool(os.getenv("OPENAI_API_KEY"))


def requires_api(func):
    """装饰器：标记需要 API 的测试"""
    return pytest.mark.skipif(
        SKIP_API_TESTS or not HAS_API_KEY,
        reason=SKIP_REASON
    )(func)


class TestVectorStore:
    """向量存储测试"""

    @requires_api
    def test_create_store(self):
        """测试创建向量存储"""
        from src.index.vector_store import VectorStore

        store = VectorStore(
            collection_name="test_collection",
            persist_directory=None  # 内存模式
        )

        assert store is not None
        assert store.collection_name == "test_collection"

    @requires_api
    def test_add_documents(self):
        """测试添加文档"""
        from src.index.vector_store import VectorStore

        store = VectorStore(collection_name="test_add", persist_directory=None)

        texts = ["Apple revenue was $416 billion", "Gross margin was 46%"]
        metadatas = [{"page": 1}, {"page": 2}]

        store.add_documents(texts=texts, metadatas=metadatas)

        assert store.count == 2

    @requires_api
    def test_search(self):
        """测试搜索"""
        from src.index.vector_store import VectorStore

        store = VectorStore(collection_name="test_search", persist_directory=None)

        texts = [
            "Apple total revenue was $416,161 million in FY2025",
            "The gross margin improved to 46.5%",
            "iPhone sales increased by 5%"
        ]
        metadatas = [{"page": 1}, {"page": 1}, {"page": 2}]

        store.add_documents(texts=texts, metadatas=metadatas)

        # 搜索
        results = store.search("total revenue", top_k=2)

        assert len(results) <= 2
        assert len(results) > 0
        # 第一个结果应该是关于 revenue 的
        assert "revenue" in results[0].text.lower() or "416" in results[0].text

    @requires_api
    def test_search_with_metadata_filter(self):
        """测试带元数据过滤的搜索"""
        from src.index.vector_store import VectorStore

        store = VectorStore(collection_name="test_filter", persist_directory=None)

        texts = [
            "2024 revenue was $390 billion",
            "2025 revenue was $416 billion"
        ]
        metadatas = [{"year": 2024}, {"year": 2025}]

        store.add_documents(texts=texts, metadatas=metadatas)

        # 只搜索 2025 年
        results = store.search("revenue", top_k=2, where={"year": 2025})

        assert len(results) >= 1
        # 结果应该是 2025 年的
        assert "416" in results[0].text

    @requires_api
    def test_search_result_structure(self):
        """测试搜索结果结构"""
        from src.index.vector_store import VectorStore

        store = VectorStore(collection_name="test_result", persist_directory=None)

        store.add_documents(
            texts=["Test document content"],
            metadatas=[{"page": 1, "source": "test.pdf"}]
        )

        results = store.search("test", top_k=1)

        assert len(results) == 1
        result = results[0]

        # 检查结果结构
        assert hasattr(result, 'text')
        assert hasattr(result, 'metadata')
        assert hasattr(result, 'score')
        assert result.metadata["page"] == 1
        assert result.metadata["source"] == "test.pdf"

    @requires_api
    def test_empty_search(self):
        """测试空结果搜索"""
        from src.index.vector_store import VectorStore

        store = VectorStore(collection_name="test_empty", persist_directory=None)

        store.add_documents(
            texts=["Apple financial data"],
            metadatas=[{"page": 1}]
        )

        # 搜索不相关的内容，使用 min_score 过滤
        results = store.search("quantum physics black hole", top_k=1, min_score=0.9)

        # 应该没有高相似度的结果
        assert len(results) == 0

    @requires_api
    def test_semantic_similarity(self):
        """测试语义相似性"""
        from src.index.vector_store import VectorStore

        store = VectorStore(collection_name="test_semantic", persist_directory=None)

        # 添加中英文文档
        texts = [
            "Apple total revenue was $416 billion",
            "苹果公司的总收入是4160亿美元",
            "The weather is sunny today"
        ]
        metadatas = [{"lang": "en"}, {"lang": "zh"}, {"lang": "en"}]

        store.add_documents(texts=texts, metadatas=metadatas)

        # 用中文搜索
        results = store.search("苹果收入", top_k=2)

        # 前两个结果应该是关于收入的（不管语言）
        texts_found = [r.text for r in results]
        assert any("revenue" in t.lower() or "收入" in t for t in texts_found)
        # 天气的那条不应该排在前面
        assert "weather" not in results[0].text.lower()


class TestVectorStoreEdgeCases:
    """向量存储边界情况测试"""

    @requires_api
    def test_duplicate_documents(self):
        """测试重复文档"""
        from src.index.vector_store import VectorStore

        store = VectorStore(collection_name="test_dup", persist_directory=None)

        # 添加相同文档两次
        store.add_documents(texts=["Same content"], metadatas=[{"page": 1}])
        store.add_documents(texts=["Same content"], metadatas=[{"page": 2}])

        # 应该有两条记录
        assert store.count == 2

    @requires_api
    def test_long_document(self):
        """测试长文档"""
        from src.index.vector_store import VectorStore

        store = VectorStore(collection_name="test_long", persist_directory=None)

        # 创建长文档
        long_text = "Apple financial report. " * 500  # 约 12000 字符

        store.add_documents(texts=[long_text], metadatas=[{"page": 1}])

        assert store.count == 1

        results = store.search("financial report", top_k=1)
        assert len(results) == 1

    @requires_api
    def test_special_characters(self):
        """测试特殊字符"""
        from src.index.vector_store import VectorStore

        store = VectorStore(collection_name="test_special", persist_directory=None)

        texts = [
            "Revenue: $416,161 million (FY2025)",
            "Growth: +5.3% YoY",
            "Ratio: 46.5%"
        ]

        store.add_documents(texts=texts, metadatas=[{"i": i} for i in range(3)])

        results = store.search("revenue growth", top_k=2)
        assert len(results) > 0


# ========== 运行测试 ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
