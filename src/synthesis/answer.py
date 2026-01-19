"""
答案格式化模块 - Answer Formatter

目的：
====
让 Agent 的回答更加规范和可追溯：
1. 支持引用标注（[1], [2] 对应检索结果）
2. 格式化输出（答案 + 来源列表）
3. 便于用户验证答案的准确性

使用方式：
========
1. Agent 在回答时使用 [1], [2] 引用检索结果
2. AnswerFormatter 解析这些引用
3. 生成包含来源信息的格式化输出

示例输出：
========
苹果公司 2025 财年的总净销售额为 416,161 百万美元 [1]。

---
来源：
[1] 第1页 - FY25_Q4_Consolidated_Financial_Statements.pdf
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Source:
    """
    来源信息

    对应检索结果中的一条记录
    """
    index: int              # 引用编号，如 1, 2, 3
    page: int               # 页码
    file: str               # 文件名
    text: str               # 原文片段
    score: float = 0.0      # 相似度分数

    def __str__(self) -> str:
        """格式化为字符串"""
        return f"[{self.index}] 第{self.page}页 - {self.file}"


@dataclass
class FormattedAnswer:
    """
    格式化后的答案

    包含：
    - 答案正文（可能包含 [1], [2] 引用标记）
    - 来源列表
    - 引用的索引
    """
    content: str                           # 答案正文
    sources: list[Source] = field(default_factory=list)  # 所有来源
    cited_indices: list[int] = field(default_factory=list)  # 答案中引用的索引

    def to_plain(self) -> str:
        """
        转为纯文本格式

        输出示例：
        苹果公司 2025 财年的总净销售额为 416,161 百万美元 [1]。

        ---
        来源：
        [1] 第1页 - FY25_Q4_Consolidated_Financial_Statements.pdf
        """
        lines = [self.content]

        if self.sources and self.cited_indices:
            lines.append("")
            lines.append("---")
            lines.append("来源：")

            for source in self.sources:
                if source.index in self.cited_indices:
                    lines.append(str(source))

        return "\n".join(lines)

    def to_markdown(self) -> str:
        """
        转为 Markdown 格式

        输出示例：
        苹果公司 2025 财年的总净销售额为 **416,161 百万美元** [1]。

        ---

        **来源：**
        - [1] 第1页 - FY25_Q4_Consolidated_Financial_Statements.pdf
        """
        lines = [self.content]

        if self.sources and self.cited_indices:
            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append("**来源：**")

            for source in self.sources:
                if source.index in self.cited_indices:
                    lines.append(f"- {source}")

        return "\n".join(lines)

    def __str__(self) -> str:
        return self.to_plain()


class AnswerFormatter:
    """
    答案格式化器

    职责：
    1. 解析检索结果，构建来源列表
    2. 解析答案中的引用标记
    3. 生成格式化输出
    """

    # 引用标记正则：匹配 [1], [2] 等
    CITATION_PATTERN = re.compile(r'\[(\d+)\]')

    def __init__(self):
        pass

    def parse_sources(self, retrieval_output: str) -> list[Source]:
        """
        解析检索工具的输出，提取来源信息

        输入格式（来自 RetrievalTool）：
        找到 3 条相关信息：

        [1] 来源: 第1页
            文件: FY25_Q4.pdf
            相似度: 0.38
            内容: Apple Inc. ...

        [2] 来源: 第4页
            ...

        返回：
            Source 对象列表
        """
        sources = []

        # 按 [数字] 分割
        parts = re.split(r'\n\[(\d+)\]', retrieval_output)

        # 跳过第一部分（"找到 X 条相关信息"）
        for i in range(1, len(parts), 2):
            if i + 1 >= len(parts):
                break

            index = int(parts[i])
            content = parts[i + 1]

            # 解析各字段
            page = self._extract_field(content, r'来源:\s*第(\d+)页', default=0)
            file = self._extract_field(content, r'文件:\s*(.+?)(?:\n|$)', default="")
            score = self._extract_field(content, r'相似度:\s*([\d.]+)', default=0.0)
            text = self._extract_field(content, r'内容:\s*(.+)', default="")

            sources.append(Source(
                index=index,
                page=int(page) if page else 0,
                file=file.strip() if file else "",
                text=text.strip() if text else "",
                score=float(score) if score else 0.0
            ))

        return sources

    def _extract_field(self, text: str, pattern: str, default=None):
        """从文本中提取字段"""
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        return default

    def extract_citations(self, answer: str) -> list[int]:
        """
        从答案中提取引用索引

        例如："总收入为 416B [1]，同比增长 5% [2]"
        返回：[1, 2]
        """
        matches = self.CITATION_PATTERN.findall(answer)
        # 去重并保持顺序
        seen = set()
        result = []
        for m in matches:
            idx = int(m)
            if idx not in seen:
                seen.add(idx)
                result.append(idx)
        return result

    def format(
        self,
        answer: str,
        retrieval_output: str = None,
        sources: list[Source] = None
    ) -> FormattedAnswer:
        """
        格式化答案

        参数：
            answer: LLM 生成的答案（可能包含 [1], [2] 引用）
            retrieval_output: 检索工具的原始输出（用于解析来源）
            sources: 或者直接传入 Source 列表

        返回：
            FormattedAnswer 对象
        """
        # 解析来源
        if sources is None and retrieval_output:
            sources = self.parse_sources(retrieval_output)
        elif sources is None:
            sources = []

        # 提取引用
        cited_indices = self.extract_citations(answer)

        return FormattedAnswer(
            content=answer,
            sources=sources,
            cited_indices=cited_indices
        )


# ========== 测试代码 ==========

if __name__ == "__main__":
    """
    运行测试：python -m src.synthesis.answer
    """

    print("=" * 60)
    print("AnswerFormatter 模块测试")
    print("=" * 60)

    # 模拟检索工具的输出
    retrieval_output = """找到 3 条相关信息：

[1] 来源: 第1页
    文件: FY25_Q4_Consolidated_Financial_Statements.pdf
    相似度: 0.38
    内容: Apple Inc. Total net sales 416,161 million...

[2] 来源: 第4页
    文件: FY25_Q4_Consolidated_Financial_Statements.pdf
    相似度: 0.31
    内容: Income before provision for income taxes...

[3] 来源: 第3页
    文件: FY25_Q4_Consolidated_Financial_Statements.pdf
    相似度: 0.31
    内容: Cash, cash equivalents, and restricted cash...
"""

    # 模拟 LLM 的答案
    answer = "苹果公司 2025 财年的总净销售额为 **416,161 百万美元** [1]。"

    # 创建格式化器
    formatter = AnswerFormatter()

    # 测试1：解析来源
    print("\n[测试 1] 解析检索输出")
    print("-" * 40)
    sources = formatter.parse_sources(retrieval_output)
    for s in sources:
        print(f"  {s}")

    # 测试2：提取引用
    print("\n[测试 2] 提取引用索引")
    print("-" * 40)
    test_answers = [
        "总收入为 416B [1]",
        "收入 [1] 和利润 [2] 都增长了",
        "这个数据来自 [1] 和 [3]，不包含 [2]",
        "没有引用的答案"
    ]
    for ans in test_answers:
        citations = formatter.extract_citations(ans)
        print(f"  '{ans[:30]}...' -> {citations}")

    # 测试3：完整格式化
    print("\n[测试 3] 完整格式化")
    print("-" * 40)
    formatted = formatter.format(answer, retrieval_output)

    print("\n纯文本格式：")
    print(formatted.to_plain())

    print("\n\nMarkdown 格式：")
    print(formatted.to_markdown())

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
