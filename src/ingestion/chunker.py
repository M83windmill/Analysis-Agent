"""
文档切分器 - Chunker

将长文档切分成适合 Embedding 的小块。

切分策略：
=========
1. 固定字符数：简单但可能切断语义
2. 固定 + 重叠：减少信息丢失
3. 按句子边界：语义完整
4. 按段落边界：主题完整（推荐）

推荐参数（财报场景）：
==================
- chunk_size: 500-1000 字符
- overlap: 50-100 字符（或 chunk_size 的 10%~20%）
- 优先按段落/句子边界切分
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Chunk:
    """
    文本块
    
    属性：
        text: 块内容
        index: 块索引（从0开始）
        metadata: 元数据（来源页码、章节等）
    """
    text: str
    index: int
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def char_count(self) -> int:
        return len(self.text)
    
    def __repr__(self) -> str:
        preview = self.text[:30].replace('\n', ' ')
        return f"Chunk({self.index}, chars={self.char_count}, '{preview}...')"


class Chunker:
    """
    文档切分器
    
    使用方法：
        chunker = Chunker(chunk_size=500, overlap=100)
        chunks = chunker.split(text)
        
        # 或者使用不同策略
        chunks = chunker.split_by_sentences(text)
        chunks = chunker.split_by_paragraphs(text)
    """
    
    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 100,
        min_chunk_size: int = 50
    ):
        """
        初始化切分器
        
        参数：
            chunk_size: 目标块大小（字符数）
            overlap: 重叠大小（字符数）
            min_chunk_size: 最小块大小，小于此值的块会被合并
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
    
    def split(
        self,
        text: str,
        metadata: dict = None
    ) -> list[Chunk]:
        """
        切分文本（默认使用段落边界 + 重叠策略）
        
        参数：
            text: 要切分的文本
            metadata: 附加到每个块的元数据
            
        返回：
            Chunk 列表
        """
        return self.split_by_paragraphs(text, metadata)
    
    def split_fixed(
        self,
        text: str,
        metadata: dict = None
    ) -> list[Chunk]:
        """固定字符数切分"""
        chunks = []
        start = 0
        index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk_meta = {**(metadata or {}), "chunk_index": index}
                chunks.append(Chunk(
                    text=chunk_text,
                    index=index,
                    metadata=chunk_meta
                ))
                index += 1
            
            start = end - self.overlap if self.overlap < self.chunk_size else end
        
        return chunks
    
    def split_by_sentences(
        self,
        text: str,
        metadata: dict = None
    ) -> list[Chunk]:
        """
        按句子边界切分
        
        保证每个块都在完整句子处结束
        """
        # 按句子分割
        sentences = re.split(r'(?<=[。！？.!?\n])\s*', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_text = []
        current_length = 0
        index = 0
        
        for sentence in sentences:
            # 如果加入这个句子会超过限制，先保存当前块
            if current_length + len(sentence) > self.chunk_size and current_text:
                chunk_content = ' '.join(current_text)
                if len(chunk_content) >= self.min_chunk_size:
                    chunk_meta = {**(metadata or {}), "chunk_index": index}
                    chunks.append(Chunk(
                        text=chunk_content,
                        index=index,
                        metadata=chunk_meta
                    ))
                    index += 1
                current_text = []
                current_length = 0
            
            current_text.append(sentence)
            current_length += len(sentence)
        
        # 保存最后一块
        if current_text:
            chunk_content = ' '.join(current_text)
            if len(chunk_content) >= self.min_chunk_size:
                chunk_meta = {**(metadata or {}), "chunk_index": index}
                chunks.append(Chunk(
                    text=chunk_content,
                    index=index,
                    metadata=chunk_meta
                ))
        
        return chunks
    
    def split_by_paragraphs(
        self,
        text: str,
        metadata: dict = None
    ) -> list[Chunk]:
        """
        按段落边界切分（推荐）
        
        每个块都是完整的段落，语义最完整
        """
        # 按双换行分割段落
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        chunks = []
        current_paras = []
        current_length = 0
        index = 0
        
        for para in paragraphs:
            # 如果加入这个段落会超过限制，先保存当前块
            if current_length + len(para) > self.chunk_size and current_paras:
                chunk_content = '\n\n'.join(current_paras)
                if len(chunk_content) >= self.min_chunk_size:
                    chunk_meta = {**(metadata or {}), "chunk_index": index}
                    chunks.append(Chunk(
                        text=chunk_content,
                        index=index,
                        metadata=chunk_meta
                    ))
                    index += 1
                current_paras = []
                current_length = 0
            
            current_paras.append(para)
            current_length += len(para)
        
        # 保存最后一块
        if current_paras:
            chunk_content = '\n\n'.join(current_paras)
            if len(chunk_content) >= self.min_chunk_size:
                chunk_meta = {**(metadata or {}), "chunk_index": index}
                chunks.append(Chunk(
                    text=chunk_content,
                    index=index,
                    metadata=chunk_meta
                ))
        
        return chunks


# ========== 便捷函数 ==========

def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100,
    strategy: str = "paragraph"
) -> list[Chunk]:
    """
    快速切分文本
    
    参数：
        text: 要切分的文本
        chunk_size: 目标块大小
        overlap: 重叠大小
        strategy: 切分策略 ("fixed", "sentence", "paragraph")
    """
    chunker = Chunker(chunk_size=chunk_size, overlap=overlap)
    
    if strategy == "fixed":
        return chunker.split_fixed(text)
    elif strategy == "sentence":
        return chunker.split_by_sentences(text)
    else:  # paragraph
        return chunker.split_by_paragraphs(text)


# ========== 测试代码 ==========

if __name__ == "__main__":
    """
    运行测试：python -m src.ingestion.chunker
    """
    import os
    
    print("=" * 60)
    print("Chunker 模块测试")
    print("=" * 60)
    
    # 加载测试文本
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sample_file = os.path.join(project_root, "data", "sample_report.txt")
    
    with open(sample_file, "r", encoding="utf-8") as f:
        text = f.read()
    
    print(f"原始文本：{len(text)} 字符")
    
    # 测试 1：默认策略（段落边界）
    print("\n【测试 1】默认策略（段落边界）")
    print("-" * 40)
    
    chunker = Chunker(chunk_size=600, overlap=50)
    chunks = chunker.split(text, metadata={"source": "sample_report.txt"})
    
    print(f"切分成 {len(chunks)} 块")
    for chunk in chunks:
        print(f"  {chunk}")
        print(f"    元数据: {chunk.metadata}")
    
    # 测试 2：固定字符数切分
    print("\n【测试 2】固定字符数切分")
    print("-" * 40)
    
    chunks_fixed = chunker.split_fixed(text)
    print(f"切分成 {len(chunks_fixed)} 块")
    for chunk in chunks_fixed[:3]:
        print(f"  {chunk}")
    
    # 测试 3：便捷函数
    print("\n【测试 3】便捷函数")
    print("-" * 40)
    
    quick_chunks = chunk_text(text, chunk_size=500, strategy="sentence")
    print(f"chunk_text() 返回 {len(quick_chunks)} 块")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

