"""
计算器工具 - Calculator Tool

这是你的第一个真正的工具！

为什么需要计算器工具？
====================
LLM 的数学能力其实很差，经常算错。比如：
- "15.7% 的 3832.85 是多少？" → LLM 可能算错
- "同比增长率 = (今年-去年)/去年" → 多步计算更容易出错

所以我们给 Agent 一个计算器工具，让它：
1. 识别出需要计算的场景
2. 调用计算器得到准确结果
3. 基于准确结果生成回答

这个工具会教你：
===============
1. 如何继承 Tool 基类
2. 如何定义参数
3. 如何实现 execute 方法
4. 如何处理错误
"""

from .base import Tool


class CalculatorTool(Tool):
    """
    计算器工具

    功能：执行数学表达式计算
    输入：数学表达式字符串，如 "100 * 0.15" 或 "(383285 - 394328) / 394328 * 100"
    输出：计算结果
    """

    @property
    def name(self) -> str:
        """
        工具名称

        命名建议：
        - 用动词或名词，清晰表达功能
        - 下划线连接
        - 这里用 "calculator" 简单直接
        """
        return "calculator"

    @property
    def description(self) -> str:
        """
        工具描述 - 最重要的部分！

        这个描述告诉 LLM：
        1. 这个工具是干什么的
        2. 什么时候应该用它
        3. 能处理什么类型的计算

        写得越清楚，LLM 越知道何时调用
        """
        return (
            "执行数学计算。"
            "当需要进行数值计算时使用，如：加减乘除、百分比、增长率、财务比率等。"
            "输入数学表达式，返回计算结果。"
            "示例：'100 * 0.15' 计算15%，'(200-150)/150*100' 计算增长率。"
        )

    @property
    def parameters(self) -> dict:
        """
        参数定义 - JSON Schema 格式

        这里只需要一个参数：expression（数学表达式）

        JSON Schema 常用类型：
        - string: 字符串
        - number: 数字（整数或浮点数）
        - integer: 整数
        - boolean: 布尔值
        - array: 数组
        - object: 对象
        """
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": (
                        "要计算的数学表达式。"
                        "支持：+、-、*、/、()、**（幂运算）。"
                        "示例：'100 * 0.44' 或 '(383285 - 394328) / 394328 * 100'"
                    )
                }
            },
            "required": ["expression"]  # expression 是必填参数
        }

    def execute(self, expression: str) -> str:
        """
        执行计算

        参数：
            expression: 数学表达式字符串

        返回：
            计算结果（字符串格式）

        安全说明：
            这里用 eval() 执行表达式，在生产环境中有安全风险。
            更安全的做法是用 ast.literal_eval 或专门的数学解析库。
            这里为了简单先用 eval，但限制了可用的函数。
        """
        try:
            # 安全检查：只允许数学运算，禁止其他代码
            # 生产环境应该用更安全的方式，这里简化处理
            allowed_chars = set("0123456789+-*/().% ")
            if not all(c in allowed_chars for c in expression):
                return f"错误：表达式包含不允许的字符。只支持数字和 +-*/().%"

            # 执行计算
            # 注意：eval 有安全风险，生产环境要用更安全的方式
            result = eval(expression)

            # 格式化结果
            if isinstance(result, float):
                # 保留合理的小数位数
                if result == int(result):
                    return str(int(result))
                else:
                    return f"{result:.4f}".rstrip('0').rstrip('.')
            else:
                return str(result)

        except ZeroDivisionError:
            return "错误：除数不能为零"
        except SyntaxError:
            return f"错误：表达式语法错误 - {expression}"
        except Exception as e:
            return f"计算错误：{str(e)}"


# ========== 测试代码 ==========

if __name__ == "__main__":
    """
    运行测试：python -m src.tools.calculator
    """
    import json

    # 创建工具实例
    calc = CalculatorTool()

    print("=" * 60)
    print("计算器工具测试")
    print("=" * 60)

    # 1. 查看工具信息
    print(f"\n工具名称: {calc.name}")
    print(f"工具描述: {calc.description}")

    # 2. 查看 OpenAI 格式
    print("\n" + "-" * 60)
    print("OpenAI 工具格式：")
    print(json.dumps(calc.to_openai_tool(), indent=2, ensure_ascii=False))

    # 3. 测试各种计算
    print("\n" + "-" * 60)
    print("计算测试：")

    test_cases = [
        ("100 + 200", "基本加法"),
        ("383285 * 0.441", "计算毛利润（收入×毛利率）"),
        ("(383285 - 394328) / 394328 * 100", "计算同比增长率"),
        ("169148 / 383285 * 100", "计算毛利率"),
        ("100 / 0", "除零错误测试"),
        ("1 + 2 * 3", "运算优先级"),
        ("(1 + 2) * 3", "括号优先级"),
    ]

    for expr, desc in test_cases:
        result = calc.execute(expression=expr)
        print(f"\n{desc}:")
        print(f"  表达式: {expr}")
        print(f"  结果: {result}")
