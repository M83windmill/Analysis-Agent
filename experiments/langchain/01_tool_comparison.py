"""
LangChain 学习 01 - Tool 定义对比

对比我们的实现 vs LangChain 的实现

运行前先安装：
    pip install langchain langchain-openai

运行方式：
    python experiments/langchain/01_tool_comparison.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

print("=" * 70)
print("Part 1: 我们的 Tool 实现")
print("=" * 70)

# ========== 我们的实现 ==========
from src.tools.base import Tool

class OurCalculator(Tool):
    """我们定义工具的方式：继承 Tool 基类"""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "计算数学表达式"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "数学表达式，如 2+2"
                }
            },
            "required": ["expression"]
        }

    def execute(self, expression: str) -> str:
        try:
            result = eval(expression)
            return f"结果: {result}"
        except Exception as e:
            return f"错误: {e}"

# 测试我们的工具
our_tool = OurCalculator()
print(f"\n工具名称: {our_tool.name}")
print(f"工具描述: {our_tool.description}")
print(f"执行 2+2: {our_tool.execute('2+2')}")
print(f"\nOpenAI 格式:")
import json
print(json.dumps(our_tool.to_openai_tool(), indent=2, ensure_ascii=False))


print("\n" + "=" * 70)
print("Part 2: LangChain 的 Tool 实现")
print("=" * 70)

# ========== LangChain 实现 ==========
try:
    from langchain_core.tools import tool, BaseTool
    from pydantic import BaseModel, Field

    # 方式 1: @tool 装饰器（最简单）
    @tool
    def lc_calculator(expression: str) -> str:
        """计算数学表达式。输入一个数学表达式如 2+2，返回计算结果。"""
        try:
            result = eval(expression)
            return f"结果: {result}"
        except Exception as e:
            return f"错误: {e}"

    print("\n方式 1: @tool 装饰器")
    print(f"工具名称: {lc_calculator.name}")
    print(f"工具描述: {lc_calculator.description}")
    print(f"执行 2+2: {lc_calculator.invoke('2+2')}")


    # 方式 2: BaseTool 类（更灵活，类似我们的实现）
    class LCCalculatorInput(BaseModel):
        """计算器输入参数"""
        expression: str = Field(description="数学表达式，如 2+2")

    class LCCalculator(BaseTool):
        """LangChain 的类式工具定义"""
        name: str = "calculator"
        description: str = "计算数学表达式"
        args_schema: type[BaseModel] = LCCalculatorInput

        def _run(self, expression: str) -> str:
            try:
                result = eval(expression)
                return f"结果: {result}"
            except Exception as e:
                return f"错误: {e}"

    print("\n方式 2: BaseTool 类")
    lc_tool = LCCalculator()
    print(f"工具名称: {lc_tool.name}")
    print(f"工具描述: {lc_tool.description}")
    print(f"执行 3*4: {lc_tool.invoke({'expression': '3*4'})}")


    print("\n" + "=" * 70)
    print("Part 3: 对比总结")
    print("=" * 70)

    print("""
┌─────────────────┬────────────────────────────────────────┐
│     我们的实现    │           LangChain 实现               │
├─────────────────┼────────────────────────────────────────┤
│ class MyTool(Tool)        │ class MyTool(BaseTool)        │
│                           │ 或 @tool 装饰器               │
├─────────────────┼────────────────────────────────────────┤
│ @property name            │ name: str = "..."             │
│ @property description     │ description: str = "..."      │
│ @property parameters      │ args_schema: BaseModel        │
├─────────────────┼────────────────────────────────────────┤
│ def execute(...)          │ def _run(...)                 │
├─────────────────┼────────────────────────────────────────┤
│ tool.execute(arg=val)     │ tool.invoke({"arg": val})     │
│                           │ 或 tool.invoke(val) 单参数    │
├─────────────────┼────────────────────────────────────────┤
│ to_openai_tool()          │ 内置支持多种格式               │
└─────────────────┴────────────────────────────────────────┘

核心区别:
1. LangChain 用 Pydantic 定义参数 schema（更强类型校验）
2. LangChain 的 @tool 装饰器从 docstring 自动提取描述
3. LangChain 支持异步 (_arun) 和回调
4. 我们的实现更轻量，LangChain 更全面
""")

except ImportError as e:
    print(f"\n❌ 需要先安装 LangChain:")
    print("   pip install langchain langchain-openai langchain-core")
    print(f"\n错误详情: {e}")


print("\n" + "=" * 70)
print("下一步: 02_agent_comparison.py - Agent 对比")
print("=" * 70)
