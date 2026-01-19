"""
LangChain 学习 02 - Agent 对比

对比我们的 ReAct Agent vs LangChain 的 AgentExecutor

运行前先安装：
    pip install langchain langchain-openai

运行方式：
    python experiments/langchain/02_agent_comparison.py
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

print("=" * 70)
print("Part 1: 我们的 Agent 实现")
print("=" * 70)

# ========== 我们的实现 ==========
from src.agent.orchestrator import AgentOrchestrator
from src.tools.calculator import CalculatorTool

print("""
我们的 AgentOrchestrator 核心逻辑 (orchestrator.py:157):

while iteration < max_iterations:
    # 1. 调用 LLM，传入工具定义
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools           # ← 工具定义
    )

    # 2. 检查是否需要调用工具
    if response.tool_calls:
        for tool_call in response.tool_calls:
            # 3. 执行工具
            result = registry.execute(tool_call.name, **args)
            # 4. 结果加入对话历史
            messages.append({"role": "tool", "content": result})
    else:
        # 5. 没有工具调用，返回最终答案
        return response.content
""")

# 运行我们的 Agent
print("\n运行我们的 Agent:")
our_agent = AgentOrchestrator(model="gpt-4o-mini", max_iterations=5, verbose=True)
our_agent.register_tool(CalculatorTool())
result = our_agent.run("计算 15 乘以 23 等于多少？")
print(f"\n最终答案: {result}")


print("\n" + "=" * 70)
print("Part 2: LangChain 的 Agent 实现 (新版 langgraph)")
print("=" * 70)

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.tools import tool
    from langgraph.prebuilt import create_react_agent

    # 定义工具
    @tool
    def calculator(expression: str) -> str:
        """计算数学表达式。输入如 15*23，返回计算结果。"""
        try:
            return str(eval(expression))
        except Exception as e:
            return f"错误: {e}"

    print("""
LangChain 新版使用 langgraph 创建 Agent:

    from langgraph.prebuilt import create_react_agent

    agent = create_react_agent(model, tools)
    result = agent.invoke({"messages": [("user", question)]})
""")

    # 创建 LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 创建 ReAct Agent（新版 API，一行搞定）
    agent = create_react_agent(llm, [calculator])

    print("运行 LangChain Agent:")
    result = agent.invoke({"messages": [("user", "计算 15 乘以 23 等于多少？")]})

    # 获取最终回答
    final_message = result["messages"][-1]
    print(f"\n最终答案: {final_message.content}")


    print("\n" + "=" * 70)
    print("Part 3: 对比总结")
    print("=" * 70)

    print("""
┌──────────────────────┬─────────────────────────────────────────┐
│      我们的实现        │      LangChain 新版 (langgraph)          │
├──────────────────────┼─────────────────────────────────────────┤
│ AgentOrchestrator    │ create_react_agent()                    │
├──────────────────────┼─────────────────────────────────────────┤
│ register_tool(tool)  │ create_react_agent(llm, [tools])        │
├──────────────────────┼─────────────────────────────────────────┤
│ agent.run(question)  │ agent.invoke({"messages": [...]})       │
├──────────────────────┼─────────────────────────────────────────┤
│ while iteration < N  │ langgraph 内部状态机管理                  │
├──────────────────────┼─────────────────────────────────────────┤
│ messages.append()    │ 自动管理 messages 历史                   │
├──────────────────────┼─────────────────────────────────────────┤
│ 手动 while 循环       │ langgraph 图结构自动循环                  │
└──────────────────────┴─────────────────────────────────────────┘

核心区别:
1. 新版 LangChain 用 langgraph 替代了 AgentExecutor
2. langgraph 是状态机/图结构，更灵活但也更抽象
3. create_react_agent 一行代码创建完整 Agent
4. 我们的 while 循环 = langgraph 的节点跳转

本质相同:
- 都是 LLM 决策 → 执行工具 → 结果反馈 → 继续决策
- 都是 ReAct 模式 (Reasoning + Acting)
""")

except ImportError as e:
    print(f"\n❌ 需要先安装 LangChain:")
    print("   pip install langchain langchain-openai")
    print(f"\n错误详情: {e}")


print("\n" + "=" * 70)
print("下一步: 03_rag_comparison.py - RAG 对比")
print("=" * 70)
