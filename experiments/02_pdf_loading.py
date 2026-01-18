"""
PDF 文档加载实验

目标：学习如何从 PDF 文件中提取文本

运行方式：python experiments/02_pdf_loading.py

实验前确保：
1. 已安装依赖：pip install pymupdf
2. 有测试 PDF 文件（或使用内置的 TXT 文件测试）

PyMuPDF 简介：
=============
PyMuPDF（fitz）是一个高性能的 PDF 处理库。
- 支持 PDF、EPUB、XPS 等格式
- 可提取文本、图片、表格
- 提取速度快，内存占用低
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    print("警告：PyMuPDF 未安装，部分功能不可用")
    print("安装命令：pip install pymupdf")


def load_pdf(pdf_path: str) -> dict:
    """
    加载 PDF 文件，提取文本和元数据

    参数：
        pdf_path: PDF 文件路径

    返回：
        {
            "metadata": {...},     # PDF 元数据
            "pages": [             # 每页内容
                {"page_num": 1, "text": "..."},
                ...
            ],
            "full_text": "..."     # 完整文本
        }
    """
    if not HAS_PYMUPDF:
        raise ImportError("需要安装 PyMuPDF: pip install pymupdf")

    doc = fitz.open(pdf_path)

    result = {
        "metadata": {
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "page_count": len(doc),
            "file_path": pdf_path
        },
        "pages": [],
        "full_text": ""
    }

    all_text = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        result["pages"].append({
            "page_num": page_num + 1,  # 1-indexed
            "text": text,
            "char_count": len(text)
        })

        all_text.append(text)

    result["full_text"] = "\n\n".join(all_text)

    doc.close()

    return result


def load_txt(txt_path: str) -> dict:
    """
    加载 TXT 文件（作为 PDF 的备选方案）

    模拟 PDF 的返回格式，方便后续流程统一处理
    """
    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 按章节分割（模拟页面）
    sections = content.split("\n\n")

    # 合并较短的段落
    pages = []
    current_page = []
    current_length = 0

    for section in sections:
        current_page.append(section)
        current_length += len(section)

        # 每 1500 字符左右作为一"页"
        if current_length > 1500:
            pages.append("\n\n".join(current_page))
            current_page = []
            current_length = 0

    if current_page:
        pages.append("\n\n".join(current_page))

    return {
        "metadata": {
            "title": os.path.basename(txt_path),
            "author": "",
            "page_count": len(pages),
            "file_path": txt_path
        },
        "pages": [
            {"page_num": i + 1, "text": text, "char_count": len(text)}
            for i, text in enumerate(pages)
        ],
        "full_text": content
    }


def load_document(file_path: str) -> dict:
    """
    统一的文档加载接口

    自动识别文件类型并调用对应的加载函数
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return load_pdf(file_path)
    elif ext in [".txt", ".md"]:
        return load_txt(file_path)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


def create_sample_pdf(output_path: str):
    """
    创建一个简单的示例 PDF 文件

    用于没有测试 PDF 时的实验
    """
    if not HAS_PYMUPDF:
        print("无法创建 PDF：PyMuPDF 未安装")
        return False

    doc = fitz.open()  # 创建空白 PDF

    # 示例内容
    pages_content = [
        """苹果公司 2023 财年年度报告

第一章：公司概况

苹果公司是一家总部位于美国加利福尼亚州库比蒂诺的跨国科技公司。
公司主要从事消费电子产品、计算机软件和在线服务的设计、开发和销售。

主要产品线：
• iPhone 智能手机
• Mac 个人电脑
• iPad 平板电脑
• Apple Watch 智能手表
• 服务（App Store、Apple Music 等）""",

        """第二章：财务亮点

2023财年关键财务指标：

总收入：383,285 百万美元
• 较2022财年下降 2.8%

毛利润：169,148 百万美元
• 毛利率：44.1%

净利润：96,995 百万美元
• 净利率：25.3%
• 每股收益：6.13 美元""",

        """第三章：分部门收入

按产品类别划分的收入：

iPhone：200,583 百万美元（52.3%）
服务：85,200 百万美元（22.2%）
Mac：29,357 百万美元（7.7%）
iPad：28,300 百万美元（7.4%）
可穿戴设备：39,845 百万美元（10.4%）"""
    ]

    for content in pages_content:
        page = doc.new_page()  # A4 尺寸
        # 在页面上写入文本
        text_point = fitz.Point(50, 50)
        page.insert_text(text_point, content, fontsize=11)

    doc.save(output_path)
    doc.close()

    print(f"已创建示例 PDF: {output_path}")
    return True


def main():
    """主实验流程"""

    print("=" * 70)
    print("实验 2: PDF 文档加载")
    print("=" * 70)

    # 确定测试文件
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 优先使用真实的财报 PDF
    real_pdf = os.path.join(project_root, "data", "FY25_Q4_Consolidated_Financial_Statements.pdf")
    sample_pdf = os.path.join(project_root, "data", "sample_report.pdf")
    sample_txt = os.path.join(project_root, "data", "sample_report.txt")

    # 检查并选择测试文件
    if os.path.exists(real_pdf):
        test_file = real_pdf
        print(f"\n使用真实财报 PDF: {real_pdf}")
    elif os.path.exists(sample_pdf):
        test_file = sample_pdf
        print(f"\n使用示例 PDF 文件: {sample_pdf}")
    elif os.path.exists(sample_txt):
        test_file = sample_txt
        print(f"\n使用 TXT 文件（PDF 不存在）: {sample_txt}")
    else:
        print("\n错误：找不到测试文件")
        print("请确保 data/ 目录下有 PDF 或 TXT 文件")
        return

    # ========== 实验 2.1: 加载文档 ==========
    print("\n【实验 2.1】加载文档")
    print("-" * 50)

    doc = load_document(test_file)

    print(f"文件路径: {doc['metadata']['file_path']}")
    print(f"标题: {doc['metadata']['title']}")
    print(f"页数: {doc['metadata']['page_count']}")
    print(f"总字符数: {len(doc['full_text'])}")

    # ========== 实验 2.2: 查看每页内容 ==========
    print("\n【实验 2.2】每页内容概览")
    print("-" * 50)

    for page in doc["pages"]:
        preview = page["text"][:100].replace("\n", " ")
        print(f"第 {page['page_num']} 页 ({page['char_count']} 字符): {preview}...")

    # ========== 实验 2.3: 提取特定页面 ==========
    print("\n【实验 2.3】提取第 1 页完整内容")
    print("-" * 50)

    if doc["pages"]:
        first_page = doc["pages"][0]
        print(f"页码: {first_page['page_num']}")
        print(f"内容预览 (前500字符):")
        print(first_page["text"][:500])

    # ========== 实验 2.4: 搜索关键词 ==========
    print("\n【实验 2.4】搜索关键词")
    print("-" * 50)

    keywords = ["毛利率", "收入", "iPhone"]

    for keyword in keywords:
        count = doc["full_text"].count(keyword)
        print(f"'{keyword}' 出现次数: {count}")

        # 找到包含关键词的页面
        pages_with_keyword = []
        for page in doc["pages"]:
            if keyword in page["text"]:
                pages_with_keyword.append(page["page_num"])

        if pages_with_keyword:
            print(f"  → 出现在第 {pages_with_keyword} 页")

    # ========== 实验 2.5: 元数据提取 ==========
    print("\n【实验 2.5】元数据")
    print("-" * 50)

    for key, value in doc["metadata"].items():
        print(f"{key}: {value}")

    # ========== 总结 ==========
    print("\n" + "=" * 70)
    print("实验总结")
    print("=" * 70)
    print("""
文档加载的关键点：
1. PyMuPDF 可以快速提取 PDF 文本
2. 按页提取便于后续标注来源（"答案来自第X页"）
3. 元数据提取帮助管理多个文档
4. 关键词搜索可用于初步验证文档内容

下一步：
- 将提取的文本进行切分（Chunking）
- 切分后才能生成 Embedding 存入向量库
""")


if __name__ == "__main__":
    main()

