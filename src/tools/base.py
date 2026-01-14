"""
工具基类 - Tool Base Class

这个文件是理解 Agent 的第一步。

核心概念：
=========
"工具" 就是 LLM 可以调用的函数。但 LLM 不能直接执行代码，
所以我们需要：
1. 用 JSON Schema 描述工具（告诉 LLM 这个工具是什么、怎么用）
2. LLM 决定要调用时，返回工具名和参数
3. 我们执行实际的函数，把结果返回给 LLM

OpenAI 的工具格式：
==================
{
    "type": "function",
    "function": {
        "name": "search_report",           # 工具名称（LLM用这个来调用）
        "description": "搜索财报中的内容",   # 描述（LLM靠这个判断何时使用）
        "parameters": {                     # 参数定义（JSON Schema格式）
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                }
            },
            "required": ["query"]
        }
    }
}

为什么要用基类？
==============
1. 统一所有工具的接口
2. 自动生成 OpenAI 需要的 JSON 格式
3. 方便管理和扩展工具
"""

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """
    工具基类

    所有工具都要继承这个类，并实现：
    1. name: 工具名称
    2. description: 工具描述（很重要！LLM靠这个判断何时使用）
    3. parameters: 参数定义
    4. execute(): 实际执行逻辑
    """

    # ========== 子类必须定义的属性 ==========

    @property
    @abstractmethod
    def name(self) -> str:
        """
        工具名称

        要求：
        - 简短、清晰
        - 用下划线连接，如 search_report, calculate_ratio
        - LLM 会用这个名称来调用工具
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        工具描述 - 这是最重要的部分！

        LLM 靠这个描述来决定：
        1. 什么时候应该用这个工具
        2. 这个工具能做什么

        好的描述示例：
        - "搜索财报中的指定内容，返回相关段落和页码"
        - "计算两个数值的比率，如毛利率、增长率等"

        差的描述示例：
        - "搜索" （太模糊，LLM不知道搜什么）
        - "这个工具很有用" （没有说明功能）
        """
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """
        参数定义 - 使用 JSON Schema 格式

        格式：
        {
            "type": "object",
            "properties": {
                "参数名": {
                    "type": "string/integer/boolean/array",
                    "description": "参数说明"
                }
            },
            "required": ["必填参数列表"]
        }

        参数描述也很重要，帮助 LLM 理解应该传什么值
        """
        pass

    # ========== 子类必须实现的方法 ==========

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """
        执行工具

        参数：
            **kwargs: LLM 传来的参数（已经解析好的）

        返回：
            str: 执行结果（会喂回给 LLM）

        注意：
        - 返回值要是字符串，LLM 才能理解
        - 如果出错，返回错误信息而不是抛异常（让 LLM 知道出了什么问题）
        """
        pass

    # ========== 转换为 OpenAI 格式 ==========

    def to_openai_tool(self) -> dict:
        """
        转换为 OpenAI API 需要的工具格式

        这个方法自动把我们定义的工具转成 OpenAI 的格式，
        你只需要定义 name, description, parameters 就行
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def __repr__(self) -> str:
        return f"Tool({self.name})"


# ========== 工具注册表 ==========

class ToolRegistry:
    """
    工具注册表 - 管理所有可用的工具

    用法：
        registry = ToolRegistry()
        registry.register(CalculatorTool())
        registry.register(SearchTool())

        # 获取所有工具的 OpenAI 格式
        tools = registry.get_openai_tools()

        # 执行某个工具
        result = registry.execute("calculator", expression="1+1")
    """

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """注册一个工具"""
        self._tools[tool.name] = tool
        print(f"已注册工具: {tool.name}")

    def get(self, name: str) -> Tool | None:
        """根据名称获取工具"""
        return self._tools.get(name)

    def get_openai_tools(self) -> list[dict]:
        """获取所有工具的 OpenAI 格式（传给 API 用）"""
        return [tool.to_openai_tool() for tool in self._tools.values()]

    def execute(self, tool_name: str, **kwargs) -> str:
        """
        执行指定的工具

        参数：
            tool_name: 工具名称
            **kwargs: 工具参数

        返回：
            执行结果
        """
        tool = self.get(tool_name)
        if tool is None:
            return f"错误: 未找到工具 '{tool_name}'"

        try:
            return tool.execute(**kwargs)
        except Exception as e:
            return f"工具执行出错: {str(e)}"

    def list_tools(self) -> list[str]:
        """列出所有已注册的工具名称"""
        return list(self._tools.keys())


# ========== 使用示例（帮助理解） ==========

if __name__ == "__main__":
    # 这段代码展示如何定义和使用工具
    # 运行: python -m src.tools.base

    # 1. 定义一个简单的工具
    class DemoTool(Tool):
        @property
        def name(self) -> str:
            return "demo_add"

        @property
        def description(self) -> str:
            return "将两个数字相加"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "第一个数字"
                    },
                    "b": {
                        "type": "number",
                        "description": "第二个数字"
                    }
                },
                "required": ["a", "b"]
            }

        def execute(self, a: float, b: float) -> str:
            result = a + b
            return f"{a} + {b} = {result}"

    # 2. 创建工具并查看 OpenAI 格式
    demo = DemoTool()
    print("=" * 50)
    print("工具名称:", demo.name)
    print("工具描述:", demo.description)
    print("\nOpenAI 格式:")
    import json
    print(json.dumps(demo.to_openai_tool(), indent=2, ensure_ascii=False))

    # 3. 测试执行
    print("\n执行测试:")
    print(demo.execute(a=10, b=20))

    # 4. 使用注册表
    print("\n" + "=" * 50)
    print("使用工具注册表:")
    registry = ToolRegistry()
    registry.register(demo)
    print("已注册工具:", registry.list_tools())
    print("执行结果:", registry.execute("demo_add", a=100, b=200))
