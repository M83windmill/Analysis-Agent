"""
Embedding 基础实验

目标：理解文本如何变成向量，体验语义相似度

运行方式：python experiments/01_embedding_basics.py

实验前确保：
1. 已安装依赖：pip install openai
2. 已配置 .env 文件中的 OPENAI_API_KEY
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def get_embedding(client: OpenAI, text: str, model: str = "text-embedding-3-small") -> list[float]:
    """
    获取文本的 embedding 向量

    参数：
        client: OpenAI 客户端
        text: 要转换的文本
        model: embedding 模型，默认 text-embedding-3-small

    返回：
        向量列表（1536维）
    """
    response = client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    计算两个向量的余弦相似度

    余弦相似度 = (A · B) / (||A|| * ||B||)

    值域：[-1, 1]
    - 1 表示完全相同方向（最相似）
    - 0 表示正交（无关）
    - -1 表示完全相反方向
    """
    # 点积
    dot_product = sum(a * b for a, b in zip(vec1, vec2))

    # 向量模长
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5

    # 余弦相似度
    return dot_product / (norm1 * norm2)


def main():
    # 检查 API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("错误：请在 .env 文件中设置 OPENAI_API_KEY")
        return

    # 初始化客户端
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )

    print("=" * 70)
    print("实验 1: Embedding 基础")
    print("=" * 70)

    # ========== 实验 1.1: 观察向量维度 ==========
    print("\n【实验 1.1】观察向量维度")
    print("-" * 50)

    text = "苹果2023年收入是3832亿美元"
    embedding = get_embedding(client, text)

    print(f"文本: {text}")
    print(f"向量维度: {len(embedding)}")
    print(f"前5个值: {embedding[:5]}")
    print(f"后5个值: {embedding[-5:]}")

    # ========== 实验 1.2: 语义相似度 - 相似句子 ==========
    print("\n【实验 1.2】语义相似度 - 相似的句子")
    print("-" * 50)

    text1 = "苹果2023年收入是3832亿美元"
    text2 = "Apple revenue in 2023 was 383 billion dollars"

    emb1 = get_embedding(client, text1)
    emb2 = get_embedding(client, text2)

    similarity = cosine_similarity(emb1, emb2)

    print(f"句子1: {text1}")
    print(f"句子2: {text2}")
    print(f"相似度: {similarity:.4f}")
    print("→ 虽然语言不同，但语义相似，所以相似度高！")

    # ========== 实验 1.3: 语义相似度 - 不相似句子 ==========
    print("\n【实验 1.3】语义相似度 - 不相似的句子")
    print("-" * 50)

    text3 = "今天天气真不错"
    emb3 = get_embedding(client, text3)

    similarity2 = cosine_similarity(emb1, emb3)

    print(f"句子1: {text1}")
    print(f"句子3: {text3}")
    print(f"相似度: {similarity2:.4f}")
    print("→ 语义完全不同，相似度低！")

    # ========== 实验 1.4: 批量对比 ==========
    print("\n【实验 1.4】批量相似度对比")
    print("-" * 50)

    query = "苹果公司的毛利率是多少"
    candidates = [
        "2023财年毛利率为44.1%，毛利润为169,148百万美元",
        "2023财年总收入为383,285百万美元",
        "iPhone是苹果最畅销的产品",
        "今天股市大涨",
    ]

    query_emb = get_embedding(client, query)

    print(f"查询: {query}\n")
    print("候选文档相似度排名：")

    results = []
    for doc in candidates:
        doc_emb = get_embedding(client, doc)
        sim = cosine_similarity(query_emb, doc_emb)
        results.append((doc, sim))

    # 按相似度排序
    results.sort(key=lambda x: x[1], reverse=True)

    for i, (doc, sim) in enumerate(results, 1):
        print(f"  {i}. [{sim:.4f}] {doc}")

    print("\n→ 这就是向量检索的原理：把查询和文档都变成向量，找最相似的！")

    # ========== 总结 ==========
    print("\n" + "=" * 70)
    print("实验总结")
    print("=" * 70)
    print("""
1. Embedding 把文本变成固定维度的向量（1536维）
2. 语义相似的文本，向量也相似（余弦相似度高）
3. 这是 RAG 检索的基础：
   - 把所有文档块变成向量存储
   - 用户提问也变成向量
   - 找最相似的文档块返回给 LLM
""")


if __name__ == "__main__":
    main()
