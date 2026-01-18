"""
Embedding 生成器 - Embedder

将文本转换为向量表示，用于语义检索。

核心概念：
=========
Embedding（嵌入）是将文本映射到高维向量空间的技术。
在这个空间中，语义相似的文本距离更近。

为什么需要 Embedding？
====================
1. 语义搜索：用户说"收入"，能找到"营收"、"revenue" 相关内容
2. 跨语言：中文问题能匹配英文文档
3. 模糊匹配：不需要完全相同的关键词

本模块提供：
==========
1. 单文本 Embedding
2. 批量 Embedding（更高效）
3. 相似度计算工具函数
"""

import os
from typing import Union
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class Embedder:
    """
    文本向量化器

    使用 OpenAI 的 Embedding 模型将文本转换为向量。

    使用方法：
        embedder = Embedder()

        # 单个文本
        vector = embedder.embed("苹果2023年收入")

        # 批量文本
        vectors = embedder.embed_batch(["文本1", "文本2", "文本3"])

        # 计算相似度
        score = embedder.similarity(vec1, vec2)
    """

    def __init__(
        self,
        model: str = None,
        api_key: str = None,
        base_url: str = None
    ):
        """
        初始化 Embedder

        参数：
            model: Embedding 模型名称，默认从环境变量读取
            api_key: OpenAI API Key，默认从环境变量读取
            base_url: API 基础 URL，用于代理
        """
        self.model = model or os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_BASE_URL")
        )

        # 缓存维度信息（首次调用时获取）
        self._dimensions = None

    @property
    def dimensions(self) -> int:
        """
        获取向量维度

        text-embedding-3-small: 1536 维
        text-embedding-3-large: 3072 维
        """
        if self._dimensions is None:
            # 通过一次调用来获取维度
            test_embedding = self.embed("test")
            self._dimensions = len(test_embedding)
        return self._dimensions

    def embed(self, text: str) -> list[float]:
        """
        将单个文本转换为向量

        参数：
            text: 要转换的文本

        返回：
            向量列表（1536维或3072维，取决于模型）
        """
        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        批量将文本转换为向量

        这比逐个调用更高效，因为：
        1. 减少 API 调用次数
        2. 降低网络延迟
        3. 可能有更好的吞吐量

        参数：
            texts: 文本列表

        返回：
            向量列表的列表，顺序与输入一致
        """
        if not texts:
            return []

        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )

        # 确保返回顺序与输入一致
        embeddings = [None] * len(texts)
        for item in response.data:
            embeddings[item.index] = item.embedding

        return embeddings

    @staticmethod
    def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """
        计算两个向量的余弦相似度

        余弦相似度 = (A · B) / (||A|| * ||B||)

        值域：[-1, 1]
        - 1: 方向完全相同（最相似）
        - 0: 正交（无关）
        - -1: 方向完全相反

        参数：
            vec1: 第一个向量
            vec2: 第二个向量

        返回：
            余弦相似度值
        """
        # 点积
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # 模长
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        # 防止除零
        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """
        计算相似度（cosine_similarity 的别名）
        """
        return self.cosine_similarity(vec1, vec2)


# ========== 便捷函数 ==========

def get_embedding(text: str, model: str = None) -> list[float]:
    """
    快速获取单个文本的 Embedding

    用于简单场景，不想创建 Embedder 实例时使用。
    """
    embedder = Embedder(model=model)
    return embedder.embed(text)


def get_embeddings(texts: list[str], model: str = None) -> list[list[float]]:
    """
    快速获取多个文本的 Embedding
    """
    embedder = Embedder(model=model)
    return embedder.embed_batch(texts)


# ========== 测试代码 ==========

if __name__ == "__main__":
    """
    运行测试：python -m src.index.embedder
    """

    print("=" * 60)
    print("Embedder 模块测试")
    print("=" * 60)

    # 创建 Embedder
    embedder = Embedder()

    # 测试 1：单个文本
    print("\n【测试 1】单个文本 Embedding")
    print("-" * 40)
    text = "苹果2023年收入是3832亿美元"
    vector = embedder.embed(text)
    print(f"文本: {text}")
    print(f"向量维度: {len(vector)}")
    print(f"前3个值: {vector[:3]}")

    # 测试 2：批量文本
    print("\n【测试 2】批量 Embedding")
    print("-" * 40)
    texts = [
        "苹果2023年收入是3832亿美元",
        "Apple revenue in 2023 was 383 billion",
        "今天天气真不错"
    ]
    vectors = embedder.embed_batch(texts)
    print(f"输入 {len(texts)} 个文本")
    print(f"输出 {len(vectors)} 个向量")
    for i, (t, v) in enumerate(zip(texts, vectors)):
        print(f"  [{i}] {t[:20]}... → 维度 {len(v)}")

    # 测试 3：相似度计算
    print("\n【测试 3】相似度计算")
    print("-" * 40)
    sim_12 = embedder.similarity(vectors[0], vectors[1])
    sim_13 = embedder.similarity(vectors[0], vectors[2])
    print(f"'{texts[0][:15]}...' vs '{texts[1][:15]}...': {sim_12:.4f}")
    print(f"'{texts[0][:15]}...' vs '{texts[2][:15]}...': {sim_13:.4f}")
    print(f"→ 语义相似的句子相似度更高！")

    # 测试 4：便捷函数
    print("\n【测试 4】便捷函数")
    print("-" * 40)
    quick_vec = get_embedding("快速测试")
    print(f"get_embedding() 返回向量维度: {len(quick_vec)}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

