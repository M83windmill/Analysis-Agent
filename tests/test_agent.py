"""
Agent 层测试 - Agent Tests

测试内容：
1. AgentOrchestrator - ReAct 循环
2. 工具调用集成

运行方式：
    pytest tests/test_agent.py -v

注意：
    部分测试需要 OpenAI API Key
    设置环境变量 SKIP_API_TESTS=1 可跳过需要 API 的测试
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json
import os

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.tools.base import Tool, ToolRegistry
from src.tools.calculator import CalculatorTool

# 检查是否跳过 API 测试
SKIP_API_TESTS = os.getenv("SKIP_API_TESTS", "0") == "1"
HAS_API_KEY = bool(os.getenv("OPENAI_API_KEY"))


def requires_api(func):
    """装饰器：标记需要 API 的测试"""
    return pytest.mark.skipif(
        SKIP_API_TESTS or not HAS_API_KEY,
        reason="SKIP_API_TESTS=1 or no API key"
    )(func)


class MockTool(Tool):
    """用于测试的 Mock 工具"""

    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "A mock tool for testing"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Test input"}
            },
            "required": ["input"]
        }

    def execute(self, input: str) -> str:
        return f"Mock result for: {input}"


class TestAgentOrchestratorUnit:
    """Agent 编排器单元测试（不需要 API）"""

    def test_create_orchestrator(self):
        """测试创建编排器"""
        from src.agent.orchestrator import AgentOrchestrator

        with patch.object(AgentOrchestrator, '__init__', lambda self, **kwargs: None):
            agent = AgentOrchestrator.__new__(AgentOrchestrator)
            agent.registry = ToolRegistry()
            agent.verbose = False

            assert agent.registry is not None

    def test_register_tool(self):
        """测试注册工具"""
        from src.agent.orchestrator import AgentOrchestrator

        with patch.object(AgentOrchestrator, '__init__', lambda self, **kwargs: None):
            agent = AgentOrchestrator.__new__(AgentOrchestrator)
            agent.registry = ToolRegistry()

            agent.registry.register(CalculatorTool())

            assert "calculator" in agent.registry.list_tools()

    def test_tool_execution_through_registry(self):
        """测试通过注册表执行工具"""
        from src.agent.orchestrator import AgentOrchestrator

        with patch.object(AgentOrchestrator, '__init__', lambda self, **kwargs: None):
            agent = AgentOrchestrator.__new__(AgentOrchestrator)
            agent.registry = ToolRegistry()
            agent.registry.register(CalculatorTool())

            result = agent.registry.execute("calculator", expression="2+2")
            assert "4" in result


class TestAgentOrchestratorIntegration:
    """Agent 编排器集成测试（需要 API）"""

    @requires_api
    def test_simple_calculation(self):
        """测试简单计算问题"""
        from src.agent.orchestrator import AgentOrchestrator

        agent = AgentOrchestrator(
            model="gpt-4o-mini",
            max_iterations=5,
            verbose=False
        )
        agent.register_tool(CalculatorTool())

        answer = agent.run("What is 15 * 23?")

        assert "345" in answer

    @requires_api
    def test_multi_step_calculation(self):
        """测试多步计算"""
        from src.agent.orchestrator import AgentOrchestrator

        agent = AgentOrchestrator(
            model="gpt-4o-mini",
            max_iterations=5,
            verbose=False
        )
        agent.register_tool(CalculatorTool())

        # 需要两步：先算 10*5，再算 结果-20
        answer = agent.run("Calculate 10 times 5, then subtract 20 from the result")

        assert "30" in answer

    @requires_api
    def test_no_tool_needed(self):
        """测试不需要工具的问题"""
        from src.agent.orchestrator import AgentOrchestrator

        agent = AgentOrchestrator(
            model="gpt-4o-mini",
            max_iterations=5,
            verbose=False
        )
        agent.register_tool(CalculatorTool())

        # 简单问题，不需要工具
        answer = agent.run("Say hello")

        assert len(answer) > 0
        # 应该直接回答，不调用工具

    @requires_api
    def test_max_iterations_limit(self):
        """测试最大迭代次数限制"""
        from src.agent.orchestrator import AgentOrchestrator

        agent = AgentOrchestrator(
            model="gpt-4o-mini",
            max_iterations=2,  # 限制为 2 次
            verbose=False
        )
        agent.register_tool(CalculatorTool())

        # 正常问题应该在 2 次内完成
        answer = agent.run("What is 2+2?")

        assert len(answer) > 0


class TestAgentWithMockLLM:
    """使用 Mock LLM 的 Agent 测试"""

    def test_tool_registry_integration(self):
        """测试工具注册表集成"""
        # 直接测试工具注册表，不需要 mock LLM
        registry = ToolRegistry()
        registry.register(CalculatorTool())

        # 测试工具执行
        result = registry.execute("calculator", expression="2+2")
        assert "4" in result

        # 测试 OpenAI 格式
        tools = registry.get_openai_tools()
        assert len(tools) == 1
        assert tools[0]["function"]["name"] == "calculator"


class TestAgentSystemPrompt:
    """系统提示词测试"""

    def test_system_prompt_contains_rules(self):
        """测试系统提示词包含规则"""
        from src.agent.orchestrator import AgentOrchestrator

        with patch('openai.OpenAI'):
            agent = AgentOrchestrator(verbose=False)

            prompt = agent._build_system_prompt()

            # 检查关键规则
            assert "工具" in prompt or "tool" in prompt.lower()
            assert "引用" in prompt or "[1]" in prompt


# ========== 运行测试 ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
