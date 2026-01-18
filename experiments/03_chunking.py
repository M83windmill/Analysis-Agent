"""
文档切分实验 - Chunking

目标：理解切分策略，选择合适的 chunk_size 和 overlap

运行方式：python experiments/03_chunking.py

为什么需要切分？
==============
1. 一页 PDF 可能有 2000+ 字符，对 Embedding 来说太大
2. 太大的块 → 语义太泛，检索不精准
3. 太小的块 → 语义不完整，缺少上下文
4. 切分是在"精准"和"完整"之间找平衡

切分策略：
=========
1. 固定字符数切分 - 简单粗暴，可能切断句子
2. 加入重叠(overlap) - 防止关键信息被切断
3. 按句子/段落边界切分 - 保持语义完整
"""

import os
import sys
import re

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 尝试导入 tiktoken 用于计算 token 数
try:
    import tiktoken
    HAS_TIKTOKEN = True
    # 使用 cl100k_base 编码（GPT-4 使用的编码）
    ENCODING = tiktoken.get_encoding("cl100k_base")
except ImportError:
    HAS_TIKTOKEN = False
    print("提示：安装 tiktoken 可以精确计算 token 数")
    print("安装命令：pip install tiktoken")


def count_tokens(text: str) -> int:
    """计算文本的 token 数"""
    if HAS_TIKTOKEN:
        return len(ENCODING.encode(text))
    else:
        # 粗略估计：英文约 4 字符/token，中文约 2 字符/token
        return len(text) // 3


# ========== 切分策略 1：固定字符数 ==========

def chunk_by_chars(text: str, chunk_size: int = 500) -> list[str]:
    """
    固定字符数切分（最简单的方法）
    
    问题：可能在句子中间切断
    "苹果公司2023年的收入是383,285百" | "万美元，同比下降2.8%"
    """
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks


# ========== 切分策略 2：固定字符数 + 重叠 ==========

def chunk_with_overlap(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """
    固定字符数 + 重叠切分
    
    overlap 的作用：让相邻块有部分重叠，防止关键信息被切断
    
    示例 (chunk_size=10, overlap=3):
    原文: "ABCDEFGHIJKLMNOP"
    块1:  "ABCDEFGHIJ"
    块2:     "HIJKLMNOP"  (H,I,J 是重叠部分)
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap  # 下一块从 overlap 之前开始
        
        # 防止无限循环
        if overlap >= chunk_size:
            break
            
    return chunks


# ========== 切分策略 3：按句子边界切分 ==========

def chunk_by_sentences(text: str, max_chunk_size: int = 500) -> list[str]:
    """
    按句子边界切分
    
    优点：不会切断句子，语义更完整
    缺点：块大小不均匀
    """
    # 按句子分割（中英文句号、问号、感叹号）
    sentences = re.split(r'(?<=[。！？.!?])\s*', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        if current_length + len(sentence) > max_chunk_size and current_chunk:
            # 当前块已满，保存并开始新块
            chunks.append(''.join(current_chunk))
            current_chunk = []
            current_length = 0
        
        current_chunk.append(sentence)
        current_length += len(sentence)
    
    # 保存最后一块
    if current_chunk:
        chunks.append(''.join(current_chunk))
    
    return chunks


# ========== 切分策略 4：按段落边界切分 ==========

def chunk_by_paragraphs(text: str, max_chunk_size: int = 1000) -> list[str]:
    """
    按段落边界切分
    
    适合结构化文档（如财报），每个段落通常是一个完整主题
    """
    # 按双换行分割段落
    paragraphs = text.split('\n\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for para in paragraphs:
        if current_length + len(para) > max_chunk_size and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = []
            current_length = 0
        
        current_chunk.append(para)
        current_length += len(para)
    
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks


def print_chunks(chunks: list[str], title: str, show_content: bool = True):
    """打印切分结果"""
    print(f"\n{title}")
    print("-" * 50)
    print(f"共 {len(chunks)} 个块")
    
    for i, chunk in enumerate(chunks):
        tokens = count_tokens(chunk)
        print(f"\n[块 {i+1}] {len(chunk)} 字符, ~{tokens} tokens")
        if show_content:
            # 显示前100字符
            preview = chunk[:100].replace('\n', ' ')
            print(f"  内容: {preview}...")
            # 显示最后50字符（看是否切断）
            ending = chunk[-50:].replace('\n', ' ')
            print(f"  结尾: ...{ending}")


def main():
    """主实验流程"""
    
    print("=" * 70)
    print("实验 3: 文档切分 (Chunking)")
    print("=" * 70)
    
    # 加载测试文本
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sample_file = os.path.join(project_root, "data", "sample_report.txt")
    
    if not os.path.exists(sample_file):
        print(f"错误：找不到测试文件 {sample_file}")
        return
    
    with open(sample_file, "r", encoding="utf-8") as f:
        text = f.read()
    
    print(f"\n原始文本：{len(text)} 字符, ~{count_tokens(text)} tokens")
    
    # ========== 实验 3.1：固定字符数切分 ==========
    print("\n" + "=" * 70)
    print("【实验 3.1】固定字符数切分 (chunk_size=500)")
    print("=" * 70)
    
    chunks_fixed = chunk_by_chars(text, chunk_size=500)
    print_chunks(chunks_fixed, "固定 500 字符切分")
    
    print("\n[!] 观察：看看结尾是否在句子中间被切断了？")
    
    # ========== 实验 3.2：加入重叠 ==========
    print("\n" + "=" * 70)
    print("【实验 3.2】固定字符数 + 重叠 (chunk_size=500, overlap=100)")
    print("=" * 70)
    
    chunks_overlap = chunk_with_overlap(text, chunk_size=500, overlap=100)
    print_chunks(chunks_overlap, "500 字符 + 100 重叠")
    
    print("\n[*] 对比：块数量变多了，但相邻块有重叠，减少信息丢失")
    
    # ========== 实验 3.3：按句子边界切分 ==========
    print("\n" + "=" * 70)
    print("【实验 3.3】按句子边界切分 (max_chunk_size=500)")
    print("=" * 70)
    
    chunks_sentence = chunk_by_sentences(text, max_chunk_size=500)
    print_chunks(chunks_sentence, "按句子边界切分")
    
    print("\n[OK] 观察：每个块都在完整句子处结束")
    
    # ========== 实验 3.4：按段落边界切分 ==========
    print("\n" + "=" * 70)
    print("【实验 3.4】按段落边界切分 (max_chunk_size=800)")
    print("=" * 70)
    
    chunks_paragraph = chunk_by_paragraphs(text, max_chunk_size=800)
    print_chunks(chunks_paragraph, "按段落边界切分")
    
    print("\n[OK] 观察：每个块都是完整的段落/章节")
    
    # ========== 实验 3.5：参数对比 ==========
    print("\n" + "=" * 70)
    print("【实验 3.5】不同 chunk_size 的对比")
    print("=" * 70)
    
    for size in [300, 500, 800, 1000]:
        chunks = chunk_with_overlap(text, chunk_size=size, overlap=size//5)
        avg_tokens = sum(count_tokens(c) for c in chunks) / len(chunks)
        print(f"chunk_size={size}, overlap={size//5}: {len(chunks)} 块, 平均 {avg_tokens:.0f} tokens/块")
    
    # ========== 总结 ==========
    print("\n" + "=" * 70)
    print("实验总结")
    print("=" * 70)
    print("""
切分策略选择指南：

1. 固定字符数：简单但可能切断语义
   → 适合：快速原型，对精度要求不高

2. 固定字符数 + 重叠：减少信息丢失
   → 适合：通用场景，推荐 overlap = chunk_size * 10%~20%

3. 按句子边界：语义完整
   → 适合：叙述性文本，如新闻、文章

4. 按段落边界：主题完整
   → 适合：结构化文档，如财报、论文

推荐参数（财报场景）：
- chunk_size: 500-1000 字符
- overlap: 50-100 字符
- 优先按段落/句子边界切分

关键理解：
- 太大的块 → 语义太泛，检索不精准
- 太小的块 → 语义不完整，缺少上下文
- 没有"最佳"参数，需要根据实际效果调整
""")


if __name__ == "__main__":
    main()

