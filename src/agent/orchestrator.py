"""
Agent 编排器 - Orchestrator (ReAct 循环)

这是 Agent 的核心引擎！

simple_agent.py 的问题：
=======================
只能调用一次工具。但真实场景需要多次调用：

问题: "苹果2023年毛利率比2022年提高了多少？"
需要:
  1. 搜索 2023 年毛利率 → 44.1%
  2. 搜索 2022 年毛利率 → 43.3%
  3. 计算差值 → 0.8%

ReAct 模式解决这个问题：
=======================
ReAct = Reasoning (推理) + Acting (行动)

循环流程：
┌─────────────────────────────────────────────────────┐
│                                                     │
│    ┌──────────┐                                     │
│    │  思考    │  "我需要先查2023年的数据..."        │
│    │ Thought  │                                     │
│    └────┬─────┘                                     │
│         │                                           │
│         ▼                                           │
│    ┌──────────┐                                     │
│    │  行动    │  调用 search_tool(year=2023)        │
│    │  Action  │                                     │
│    └────┬─────┘                                     │
│         │                                           │
│         ▼                                           │
│    ┌──────────┐                                     │
│    │  观察    │  "找到了：2023年毛利率44.1%"        │
│    │Observation│                                    │
│    └────┬─────┘                                     │
│         │                                           │
│         ▼                                           │
│    继续循环，直到 LLM 认为信息足够，给出最终答案     │
│                                                     │
└─────────────────────────────────────────────────────┘

关键设计：
=========
1. 最大迭代次数 - 防止死循环
2. 完整的对话历史 - 让 LLM 知道之前做了什么
3. 清晰的日志 - 方便调试和理解
"""

import json
import os
from typing import Generator
from openai import OpenAI
from dotenv import load_dotenv

from src.tools.base import Tool, ToolRegistry
from src.tools.calculator import CalculatorTool

load_dotenv()


class AgentOrchestrator:
    """
    Agent 编排器 - 实现 ReAct 循环

    核心职责：
    1. 管理对话历史
    2. 协调 LLM 和工具的交互
    3. 控制循环流程
    4. 防止死循环
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        max_iterations: int = 10,
        verbose: bool = True
    ):
        """
        初始化编排器

        参数：
            model: 使用的模型
            max_iterations: 最大迭代次数（防止死循环）
            verbose: 是否打印详细日志
        """
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        self.model = model
        self.max_iterations = max_iterations
        self.verbose = verbose

        # 工具注册表
        self.registry = ToolRegistry()

        # System Prompt - 指导 Agent 行为
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """
        构建 System Prompt

        好的 System Prompt 应该包含：
        1. 角色定义
        2. 任务说明
        3. 行为规则
        4. 输出格式要求
        """
        return """你是一个专业的财务分析助手。

## 你的能力
你可以使用工具来：
- 搜索财报内容
- 执行数学计算
- 提取表格数据

## 工作流程
1. 分析用户问题，确定需要哪些信息
2. 使用工具获取所需数据
3. 基于获取的数据进行分析
4. 给出准确、有依据的回答

## 重要规则
1. **必须使用工具**：进行数学计算时，必须使用 calculator 工具，不要心算
2. **多步思考**：复杂问题要分步骤解决，每次获取一部分信息
3. **基于证据**：回答必须基于工具返回的数据，不要编造数字
4. **承认不足**：如果找不到数据，诚实告诉用户，不要猜测

## 引用规则（重要！）
当你使用搜索工具获取信息后，在回答中必须标注来源：
- 使用 [1], [2], [3] 等标记引用对应的搜索结果
- 例如："苹果公司2025财年总净销售额为416,161百万美元 [1]"
- 每个数据点都应标注来源，便于用户核实

## 输出格式
- 回答要简洁清晰
- 涉及数字要给出计算过程
- 重要结论用数据支撑
- 使用 [n] 标注数据来源
"""

    def register_tool(self, tool: Tool) -> None:
        """注册工具"""
        self.registry.register(tool)

    def _log(self, message: str, level: str = "INFO") -> None:
        """打印日志"""
        if self.verbose:
            prefix = {
                "INFO": "[INFO]",
                "ACTION": "[ACTION]",
                "RESULT": "[RESULT]",
                "THINK": "[THINK]",
                "DONE": "[DONE]",
                "WARN": "[WARN]",
                "ERROR": "[ERROR]"
            }.get(level, "")
            print(f"{prefix} {message}")

    def run(self, user_question: str) -> str:
        """
        运行 Agent - ReAct 循环的主入口

        这是核心方法，实现了完整的 ReAct 循环：
        1. 初始化对话
        2. 循环：调用LLM → 执行工具 → 更新对话
        3. 直到 LLM 给出最终答案或达到最大迭代次数

        参数：
            user_question: 用户问题

        返回：
            Agent 的最终回答
        """
        if self.verbose:
            print("\n" + "=" * 70)
            print(f"[QUESTION] {user_question}")
            print("=" * 70)

        # ========== 初始化对话历史 ==========
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_question}
        ]

        # 获取工具定义
        tools = self.registry.get_openai_tools()

        # ========== ReAct 循环 ==========
        for iteration in range(1, self.max_iterations + 1):
            if self.verbose:
                print(f"\n{'-' * 70}")
                print(f"[ITERATION {iteration}]")
                print(f"{'-' * 70}")

            # ----- 步骤1: 调用 LLM -----
            self._log("调用 LLM 思考下一步...", "THINK")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            assistant_message = response.choices[0].message

            # ----- 步骤2: 检查是否需要调用工具 -----
            if assistant_message.tool_calls:
                # LLM 决定调用工具
                self._log(f"LLM 决定调用 {len(assistant_message.tool_calls)} 个工具", "ACTION")

                # 把 LLM 的消息加入历史
                messages.append(assistant_message)

                # 执行每个工具调用
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    self._log(f"工具: {tool_name}", "ACTION")
                    self._log(f"参数: {json.dumps(tool_args, ensure_ascii=False)}", "ACTION")

                    # ----- 步骤3: 执行工具 -----
                    result = self.registry.execute(tool_name, **tool_args)
                    self._log(f"结果: {result}", "RESULT")

                    # ----- 步骤4: 把工具结果加入对话 -----
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })

                # 继续循环，让 LLM 处理工具结果

            else:
                # LLM 没有调用工具，说明准备好回答了
                final_answer = assistant_message.content
                self._log("LLM 生成最终答案", "DONE")

                if self.verbose:
                    print(f"\n{'=' * 70}")
                    print(f"[FINAL ANSWER]")
                    print(f"{'=' * 70}")
                    print(final_answer)
                    print(f"{'=' * 70}")
                    print(f"[STATS] Total iterations: {iteration}")

                return final_answer

        # ========== 达到最大迭代次数 ==========
        self._log(f"达到最大迭代次数 ({self.max_iterations})，强制结束", "WARN")

        # 强制让 LLM 总结
        messages.append({
            "role": "user",
            "content": "请根据目前收集到的信息，给出你的最终答案。如果信息不足，请说明。"
        })

        final_response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )

        return final_response.choices[0].message.content

    def run_with_history(self, user_question: str, history: list = None) -> tuple[str, list]:
        """
        带对话历史的运行（支持多轮对话）

        参数：
            user_question: 用户问题
            history: 之前的对话历史

        返回：
            (答案, 更新后的历史)
        """
        # 如果没有历史，初始化
        if history is None:
            history = [{"role": "system", "content": self.system_prompt}]

        # 添加用户问题
        history.append({"role": "user", "content": user_question})

        # 运行（简化版，实际应该复用上面的循环逻辑）
        answer = self.run(user_question)

        # 添加助手回答
        history.append({"role": "assistant", "content": answer})

        return answer, history


# ========== 创建一个模拟的检索工具（用于测试多轮调用） ==========

class MockSearchTool(Tool):
    """
    模拟检索工具 - 用于演示多轮调用

    在真实场景中，这里会连接向量数据库进行语义检索
    现在我们用硬编码的数据来演示
    """

    # 模拟的财报数据
    MOCK_DATA = {
        "2023_毛利率": "2023财年毛利率为44.1%，毛利润169,148百万美元",
        "2022_毛利率": "2022财年毛利率为43.3%，毛利润170,782百万美元",
        "2023_收入": "2023财年总收入383,285百万美元",
        "2022_收入": "2022财年总收入394,328百万美元",
        "2023_净利润": "2023财年净利润96,995百万美元，净利率25.3%",
        "2022_净利润": "2022财年净利润99,803百万美元，净利率25.3%",
        "2023_iPhone": "2023财年iPhone收入200,583百万美元，占总收入52.3%",
        "2023_服务": "2023财年服务收入85,200百万美元，同比增长9.1%",
    }

    @property
    def name(self) -> str:
        return "search_report"

    @property
    def description(self) -> str:
        return (
            "搜索财务报告中的信息。"
            "输入要查询的关键词和年份，返回相关的财务数据。"
            "可以查询：收入、毛利率、净利润、各产品线收入等。"
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词，如：毛利率、收入、净利润、iPhone收入"
                },
                "year": {
                    "type": "integer",
                    "description": "财年年份，如：2023、2022"
                }
            },
            "required": ["query"]
        }

    def execute(self, query: str, year: int = None) -> str:
        """执行搜索"""
        # 构建搜索键
        query_lower = query.lower()

        # 简单的关键词匹配
        results = []
        for key, value in self.MOCK_DATA.items():
            key_year = key.split("_")[0]
            key_topic = key.split("_")[1]

            # 年份过滤
            if year and str(year) != key_year:
                continue

            # 关键词匹配
            if query_lower in key_topic or query_lower in value.lower():
                results.append(value)

        if results:
            return "\n".join(results)
        else:
            return f"未找到关于 '{query}' (年份: {year}) 的信息"


# ========== 测试代码 ==========

if __name__ == "__main__":
    """
    运行测试：python -m src.agent.orchestrator
    """

    # 检查 API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("错误：请在 .env 文件中设置 OPENAI_API_KEY")
        exit(1)

    # 创建编排器
    orchestrator = AgentOrchestrator(
        model="gpt-4o-mini",
        max_iterations=10,
        verbose=True
    )

    # 注册工具
    orchestrator.register_tool(CalculatorTool())
    orchestrator.register_tool(MockSearchTool())

    print("\n" + "#" * 70)
    print("# ReAct Agent 测试")
    print("#" * 70)

    # 测试问题 - 需要多轮调用
    test_questions = [
        # 问题1：需要搜索 + 搜索 + 计算 (3轮)
        "苹果2023年的毛利率比2022年提高了多少个百分点？",

        # 问题2：需要搜索 + 计算 (2轮)
        # "苹果2023年iPhone收入占总收入的百分比是多少？实际计算验证一下。",
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n\n{'#' * 70}")
        print(f"# 测试 {i}: {question[:50]}...")
        print(f"{'#' * 70}")

        answer = orchestrator.run(question)
