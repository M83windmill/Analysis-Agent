"""
文档加载器 - Document Loader

从各种格式的文件中提取文本内容。

支持格式：
=========
- PDF: 使用 PyMuPDF 提取
- TXT/MD: 直接读取文本
- (未来可扩展 HTML、DOCX 等)

核心功能：
=========
1. 统一的加载接口
2. 按页/章节提取
3. 元数据提取（标题、作者、页码等）
4. 自动识别文件类型
"""

import os
from dataclasses import dataclass, field
from typing import Optional

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


@dataclass
class Page:
    """
    文档页面

    属性：
        page_num: 页码（从1开始）
        text: 页面文本内容
        metadata: 页面级别的元数据
    """
    page_num: int
    text: str
    metadata: dict = field(default_factory=dict)

    @property
    def char_count(self) -> int:
        """字符数"""
        return len(self.text)

    def __repr__(self) -> str:
        preview = self.text[:50].replace("\n", " ")
        return f"Page({self.page_num}, chars={self.char_count}, '{preview}...')"


@dataclass
class Document:
    """
    加载后的文档

    属性：
        pages: 页面列表
        metadata: 文档级别的元数据
        source: 源文件路径
    """
    pages: list[Page]
    metadata: dict
    source: str

    @property
    def page_count(self) -> int:
        """页数"""
        return len(self.pages)

    @property
    def full_text(self) -> str:
        """完整文本（所有页面拼接）"""
        return "\n\n".join(page.text for page in self.pages)

    @property
    def total_chars(self) -> int:
        """总字符数"""
        return sum(page.char_count for page in self.pages)

    def get_page(self, page_num: int) -> Optional[Page]:
        """获取指定页码的页面（页码从1开始）"""
        for page in self.pages:
            if page.page_num == page_num:
                return page
        return None

    def search(self, keyword: str) -> list[tuple[int, str]]:
        """
        搜索关键词

        返回：包含关键词的页面列表 [(页码, 相关段落), ...]
        """
        results = []
        for page in self.pages:
            if keyword in page.text:
                # 提取包含关键词的段落
                for para in page.text.split("\n\n"):
                    if keyword in para:
                        results.append((page.page_num, para.strip()))
        return results

    def __repr__(self) -> str:
        return f"Document(source='{os.path.basename(self.source)}', pages={self.page_count}, chars={self.total_chars})"


class DocumentLoader:
    """
    文档加载器

    统一的文档加载接口，自动识别文件类型。

    使用方法：
        loader = DocumentLoader()
        doc = loader.load("path/to/file.pdf")

        print(doc.page_count)
        print(doc.pages[0].text)
        print(doc.full_text)
    """

    # 支持的文件类型
    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}

    def load(self, file_path: str) -> Document:
        """
        加载文档

        参数：
            file_path: 文件路径

        返回：
            Document 对象
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"不支持的文件格式: {ext}。"
                f"支持的格式: {self.SUPPORTED_EXTENSIONS}"
            )

        if ext == ".pdf":
            return self._load_pdf(file_path)
        else:  # .txt, .md
            return self._load_text(file_path)

    def _load_pdf(self, file_path: str) -> Document:
        """加载 PDF 文件"""
        if not HAS_PYMUPDF:
            raise ImportError(
                "需要安装 PyMuPDF 才能加载 PDF 文件。"
                "安装命令: pip install pymupdf"
            )

        doc = fitz.open(file_path)

        pages = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            pages.append(Page(
                page_num=page_num + 1,  # 1-indexed
                text=text,
                metadata={"source_page": page_num + 1}
            ))

        metadata = {
            "title": doc.metadata.get("title", "") or os.path.basename(file_path),
            "author": doc.metadata.get("author", ""),
            "format": "pdf",
            "page_count": len(doc),
            "file_size": os.path.getsize(file_path)
        }

        doc.close()

        return Document(
            pages=pages,
            metadata=metadata,
            source=file_path
        )

    def _load_text(self, file_path: str) -> Document:
        """
        加载文本文件

        将文本按段落分组，模拟"页面"结构
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 按章节/大段落分割
        sections = self._split_into_sections(content)

        pages = []
        for i, section in enumerate(sections):
            pages.append(Page(
                page_num=i + 1,
                text=section,
                metadata={"source_section": i + 1}
            ))

        metadata = {
            "title": os.path.basename(file_path),
            "author": "",
            "format": "txt",
            "page_count": len(pages),
            "file_size": os.path.getsize(file_path)
        }

        return Document(
            pages=pages,
            metadata=metadata,
            source=file_path
        )

    def _split_into_sections(
        self,
        text: str,
        min_section_length: int = 500,
        max_section_length: int = 2000
    ) -> list[str]:
        """
        将文本分割成章节

        规则：
        1. 优先按 "第X章"、"Chapter" 等标记分割
        2. 其次按大段落（双换行）分割
        3. 合并过短的段落，截断过长的段落
        """
        # 按双换行分割
        paragraphs = text.split("\n\n")

        sections = []
        current_section = []
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 检查是否是章节标题
            is_chapter_header = (
                para.startswith("第") and "章" in para[:10] or
                para.lower().startswith("chapter") or
                para.startswith("=") or
                para.startswith("#")
            )

            # 如果是新章节且当前有内容，保存当前部分
            if is_chapter_header and current_section and current_length > min_section_length:
                sections.append("\n\n".join(current_section))
                current_section = []
                current_length = 0

            current_section.append(para)
            current_length += len(para)

            # 如果当前部分已经够长，保存
            if current_length >= max_section_length:
                sections.append("\n\n".join(current_section))
                current_section = []
                current_length = 0

        # 保存剩余内容
        if current_section:
            sections.append("\n\n".join(current_section))

        return sections


# ========== 便捷函数 ==========

def load_document(file_path: str) -> Document:
    """
    快速加载文档

    用于不想创建 DocumentLoader 实例的简单场景
    """
    loader = DocumentLoader()
    return loader.load(file_path)


# ========== 测试代码 ==========

if __name__ == "__main__":
    """
    运行测试：python -m src.ingestion.loader
    """
    import os

    print("=" * 60)
    print("DocumentLoader 模块测试")
    print("=" * 60)

    # 找到测试文件
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    test_file = os.path.join(project_root, "data", "sample_report.txt")

    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        exit(1)

    # 测试 1：加载文档
    print("\n【测试 1】加载文档")
    print("-" * 40)

    loader = DocumentLoader()
    doc = loader.load(test_file)

    print(f"文档: {doc}")
    print(f"来源: {doc.source}")
    print(f"页数: {doc.page_count}")
    print(f"总字符数: {doc.total_chars}")

    # 测试 2：查看页面
    print("\n【测试 2】页面预览")
    print("-" * 40)

    for page in doc.pages[:3]:  # 只显示前3页
        print(f"  {page}")

    # 测试 3：搜索关键词
    print("\n【测试 3】搜索关键词")
    print("-" * 40)

    results = doc.search("毛利率")
    print(f"搜索 '毛利率'，找到 {len(results)} 处:")
    for page_num, para in results[:2]:  # 只显示前2个结果
        print(f"  [第{page_num}页] {para[:80]}...")

    # 测试 4：便捷函数
    print("\n【测试 4】便捷函数")
    print("-" * 40)

    doc2 = load_document(test_file)
    print(f"load_document() 返回: {doc2}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

