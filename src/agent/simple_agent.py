"""
最简单的 Agent - Simple Agent

这个文件是理解 Agent 的核心！！！

它展示了完整的工具调用流程：
===============================
1. 用户提问
2. 把问题 + 工具定义 发给 LLM
3. LLM 决定是否需要调用工具
   - 如果需要：返回工具名和参数
   - 如果不需要：直接返回答案
4. 我们执行工具，获得结果
5. 把工具结果喂回给 LLM
6. LLM 基于工具结果生成最终答案

这就是 Agent 的本质：LLM + 工具调用循环
"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# 导入我们的工具
from src.tools.base import ToolRegistry
from src.tools.calculator import CalculatorTool


# 加载环境变量（API Key）
load_dotenv()


class SimpleAgent:
    """
    最简单的 Agent 实现

    这个类只做一件事：让 LLM 能够调用工具

    使用方法：
        agent = SimpleAgent()
        answer = agent.run("苹果收入383285百万，毛利率44.1%，毛利润是多少？")
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        """
        初始化 Agent

        参数：
            model: 使用的模型，默认 gpt-4o-mini（便宜够用）
        """
        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")  # 如果用代理可以设置
        )
        self.model = model

        # 初始化工具注册表
        self.registry = ToolRegistry()

        # 注册工具 - 目前只有计算器
        self.registry.register(CalculatorTool())

        # System Prompt - 告诉 LLM 它的角色和规则
        self.system_prompt = """你是一个财务分析助手。

你的任务是回答用户关于财务数据的问题。

重要规则：
1. 当需要进行数学计算时，必须使用 calculator 工具，不要自己心算
2. 回答要简洁准确
3. 如果计算出错，告诉用户具体问题

你可以使用的工具：
- calculator: 执行数学计算
"""

    def run(self, user_question: str) -> str:
        """
        运行 Agent

        这是核心方法，展示了完整的工具调用流程

        参数：
            user_question: 用户的问题

        返回：
            Agent 的回答
        """
        print("\n" + "=" * 60)
        print(f"用户问题: {user_question}")
        print("=" * 60)

        # ========== 第1步：准备消息 ==========
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_question}
        ]

        # ========== 第2步：获取工具定义 ==========
        # 把我们的工具转成 OpenAI API 需要的格式
        tools = self.registry.get_openai_tools()

        print("\n[步骤1] 发送请求给 LLM...")
        print(f"  - 模型: {self.model}")
        print(f"  - 可用工具: {self.registry.list_tools()}")

        # ========== 第3步：调用 LLM ==========
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,           # 传入工具定义
            tool_choice="auto"     # 让 LLM 自己决定是否使用工具
        )

        # 获取 LLM 的回复
        assistant_message = response.choices[0].message

        # ========== 第4步：检查是否需要调用工具 ==========
        if assistant_message.tool_calls:
            # LLM 决定要调用工具！
            print("\n[步骤2] LLM 决定调用工具:")

            # 把 LLM 的消息加入对话历史
            messages.append(assistant_message)

            # 处理每个工具调用（可能有多个）
            for tool_call in assistant_message.tool_calls:
                # 解析工具调用信息
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                print(f"  - 工具: {tool_name}")
                print(f"  - 参数: {tool_args}")

                # ========== 第5步：执行工具 ==========
                print(f"\n[步骤3] 执行工具 {tool_name}...")
                tool_result = self.registry.execute(tool_name, **tool_args)
                print(f"  - 结果: {tool_result}")

                # ========== 第6步：把工具结果加入对话 ==========
                # 注意格式：role 必须是 "tool"，要带上 tool_call_id
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })

            # ========== 第7步：让 LLM 基于工具结果生成最终答案 ==========
            print("\n[步骤4] LLM 根据工具结果生成答案...")

            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )

            final_answer = final_response.choices[0].message.content

        else:
            # LLM 决定不使用工具，直接回答
            print("\n[步骤2] LLM 决定直接回答（不使用工具）")
            final_answer = assistant_message.content

        print("\n" + "-" * 60)
        print(f"最终答案: {final_answer}")
        print("-" * 60)

        return final_answer


# ========== 测试代码 ==========

if __name__ == "__main__":
    """
    运行测试：python -m src.agent.simple_agent

    确保先设置好 .env 文件中的 OPENAI_API_KEY
    """

    # 检查 API Key
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("错误：请在 .env 文件中设置 OPENAI_API_KEY")
        print("参考 .env.example 文件")
        exit(1)

    # 创建 Agent
    agent = SimpleAgent()

    # 测试问题
    test_questions = [
        # 问题1：需要计算
        "苹果2023年收入是383285百万美元，毛利率是44.1%，请计算毛利润是多少？",

        # 问题2：计算增长率
        "去年收入394328百万，今年收入383285百万，同比增长率是多少？",

        # 问题3：不需要计算
        "什么是毛利率？",
    ]

    print("\n" + "=" * 60)
    print("Simple Agent 测试")
    print("=" * 60)

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'#' * 60}")
        print(f"# 测试 {i}")
        print(f"{'#' * 60}")

        answer = agent.run(question)

        print(f"\n>>> 问题: {question}")
        print(f">>> 答案: {answer}")

        # 分隔线
        print("\n")
