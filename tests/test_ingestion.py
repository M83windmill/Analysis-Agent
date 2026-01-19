"""
摄取层测试 - Ingestion Tests

测试内容：
1. DocumentLoader - 文档加载
2. Chunker - 文档切分

运行方式：
    pytest tests/test_ingestion.py -v
"""

import pytest
import tempfile
import os

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingestion.loader import DocumentLoader, Document, Page
from src.ingestion.chunker import Chunker, Chunk


class TestDocumentLoader:
    """文档加载器测试"""

    def setup_method(self):
        """每个测试前创建新实例"""
        self.loader = DocumentLoader()

    def test_load_txt_file(self):
        """测试加载 TXT 文件"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("This is a test document.\nIt has multiple lines.")
            temp_path = f.name

        try:
            doc = self.loader.load(temp_path)

            assert isinstance(doc, Document)
            assert doc.page_count >= 1
            assert "test document" in doc.full_text
            assert doc.metadata["format"] == "txt"
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        with pytest.raises(FileNotFoundError):
            self.loader.load("/nonexistent/path/file.txt")

    def test_document_properties(self):
        """测试 Document 属性"""
        pages = [
            Page(page_num=1, text="Page one content"),
            Page(page_num=2, text="Page two content")
        ]
        doc = Document(pages=pages, metadata={"title": "Test"}, source="test.txt")

        assert doc.page_count == 2
        assert doc.total_chars == len("Page one content") + len("Page two content")
        assert "Page one" in doc.full_text
        assert "Page two" in doc.full_text

    def test_page_properties(self):
        """测试 Page 属性"""
        page = Page(page_num=1, text="Hello World")

        assert page.page_num == 1
        assert page.char_count == 11
        assert page.text == "Hello World"


class TestChunker:
    """文档切分器测试"""

    def test_basic_chunking(self):
        """测试基本切分"""
        chunker = Chunker(chunk_size=50, overlap=10)
        text = "A" * 200  # 200 个字符，确保产生多个块

        chunks = chunker.split(text)

        assert len(chunks) >= 1
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_chunk_size(self):
        """测试切分大小"""
        chunker = Chunker(chunk_size=100, overlap=0)
        text = "A" * 250

        chunks = chunker.split(text)

        # 大多数块应该接近 chunk_size
        for chunk in chunks[:-1]:  # 最后一块可能较小
            assert chunk.char_count <= 100

    def test_overlap(self):
        """测试重叠"""
        chunker = Chunker(chunk_size=50, overlap=10)
        text = "ABCDEFGHIJ" * 10  # 100 字符

        chunks = chunker.split(text)

        # 如果有多个块，检查重叠
        if len(chunks) >= 2:
            # 第一个块的结尾应该出现在第二个块的开头附近
            end_of_first = chunks[0].text[-10:]
            assert end_of_first in chunks[1].text

    def test_metadata_preserved(self):
        """测试元数据保留"""
        chunker = Chunker(chunk_size=50, overlap=0)
        metadata = {"page": 1, "source": "test.pdf"}

        chunks = chunker.split("A" * 100, metadata=metadata)

        for chunk in chunks:
            assert chunk.metadata["page"] == 1
            assert chunk.metadata["source"] == "test.pdf"

    def test_min_chunk_size(self):
        """测试最小块大小"""
        chunker = Chunker(chunk_size=100, overlap=0, min_chunk_size=20)

        # 大于 min_chunk_size 的文本
        chunks = chunker.split("This is a longer text that should be kept")

        # 应该返回一个块
        assert len(chunks) >= 1

    def test_empty_text(self):
        """测试空文本"""
        chunker = Chunker(chunk_size=100, overlap=0)
        chunks = chunker.split("")

        assert len(chunks) == 0

    def test_paragraph_split(self):
        """测试段落切分"""
        chunker = Chunker(chunk_size=100, overlap=0)
        text = "Paragraph one content here.\n\nParagraph two content here.\n\nParagraph three."

        chunks = chunker.split(text)

        # 应该产生块
        assert len(chunks) >= 1

    def test_chunk_index(self):
        """测试块索引"""
        chunker = Chunker(chunk_size=30, overlap=0)
        chunks = chunker.split("A" * 100)

        # 检查索引是否正确
        for i, chunk in enumerate(chunks):
            assert chunk.metadata.get("chunk_index") == i


class TestChunk:
    """Chunk 数据类测试"""

    def test_chunk_properties(self):
        """测试 Chunk 属性"""
        chunk = Chunk(
            text="Hello World",
            index=0,
            metadata={"page": 1}
        )

        assert chunk.char_count == 11
        assert chunk.text == "Hello World"
        assert chunk.metadata["page"] == 1
        assert chunk.index == 0


class TestIntegration:
    """集成测试：加载 + 切分"""

    def test_load_and_chunk(self):
        """测试加载后切分"""
        # 创建临时文件
        content = "This is paragraph one. " * 20 + "\n\n" + "This is paragraph two. " * 20
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name

        try:
            loader = DocumentLoader()
            chunker = Chunker(chunk_size=100, overlap=20)

            doc = loader.load(temp_path)
            all_chunks = []
            for page in doc.pages:
                chunks = chunker.split(page.text, metadata={"page": page.page_num})
                all_chunks.extend(chunks)

            assert len(all_chunks) > 1
            # 所有块都应该有 page 元数据
            for chunk in all_chunks:
                assert "page" in chunk.metadata

        finally:
            os.unlink(temp_path)


# ========== 运行测试 ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
