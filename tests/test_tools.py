"""
工具层测试 - Tools Tests

测试内容：
1. CalculatorTool - 数学计算
2. RetrievalTool - 检索工具（需要 mock VectorStore）
3. ToolRegistry - 工具注册表

运行方式：
    pytest tests/test_tools.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.base import Tool, ToolRegistry
from src.tools.calculator import CalculatorTool


class TestCalculatorTool:
    """计算器工具测试"""

    def setup_method(self):
        """每个测试前创建新实例"""
        self.calc = CalculatorTool()

    def test_name(self):
        """测试工具名称"""
        assert self.calc.name == "calculator"

    def test_description(self):
        """测试工具描述"""
        assert "计算" in self.calc.description or "数学" in self.calc.description

    def test_parameters(self):
        """测试参数定义"""
        params = self.calc.parameters
        assert params["type"] == "object"
        assert "expression" in params["properties"]

    def test_basic_addition(self):
        """测试基本加法"""
        result = self.calc.execute("1 + 1")
        assert "2" in result

    def test_basic_subtraction(self):
        """测试基本减法"""
        result = self.calc.execute("10 - 3")
        assert "7" in result

    def test_multiplication(self):
        """测试乘法"""
        result = self.calc.execute("6 * 7")
        assert "42" in result

    def test_division(self):
        """测试除法"""
        result = self.calc.execute("100 / 4")
        assert "25" in result

    def test_complex_expression(self):
        """测试复杂表达式"""
        result = self.calc.execute("(100 - 60) / 100 * 100")
        assert "40" in result

    def test_percentage_calculation(self):
        """测试百分比计算（毛利率场景）"""
        # 毛利率 = (收入 - 成本) / 收入 * 100
        result = self.calc.execute("(416161 - 223119) / 416161 * 100")
        # 结果约 46.4%
        assert "46" in result

    def test_division_by_zero(self):
        """测试除零错误"""
        result = self.calc.execute("1 / 0")
        assert "错误" in result or "error" in result.lower()

    def test_invalid_expression(self):
        """测试无效表达式"""
        result = self.calc.execute("abc + def")
        assert "错误" in result or "error" in result.lower()

    def test_openai_tool_format(self):
        """测试 OpenAI 工具格式"""
        tool_def = self.calc.to_openai_tool()
        assert tool_def["type"] == "function"
        assert tool_def["function"]["name"] == "calculator"
        assert "parameters" in tool_def["function"]


class TestToolRegistry:
    """工具注册表测试"""

    def setup_method(self):
        """每个测试前创建新实例"""
        self.registry = ToolRegistry()

    def test_register_tool(self):
        """测试注册工具"""
        calc = CalculatorTool()
        self.registry.register(calc)
        assert "calculator" in self.registry.list_tools()

    def test_get_tool(self):
        """测试获取工具"""
        calc = CalculatorTool()
        self.registry.register(calc)
        retrieved = self.registry.get("calculator")
        assert retrieved is calc

    def test_get_nonexistent_tool(self):
        """测试获取不存在的工具"""
        result = self.registry.get("nonexistent")
        assert result is None

    def test_execute_tool(self):
        """测试执行工具"""
        calc = CalculatorTool()
        self.registry.register(calc)
        result = self.registry.execute("calculator", expression="2 + 2")
        assert "4" in result

    def test_execute_nonexistent_tool(self):
        """测试执行不存在的工具"""
        result = self.registry.execute("nonexistent", arg="value")
        assert "未找到" in result or "not found" in result.lower()

    def test_list_tools(self):
        """测试列出所有工具"""
        self.registry.register(CalculatorTool())
        tools = self.registry.list_tools()
        assert isinstance(tools, list)
        assert "calculator" in tools

    def test_get_openai_tools(self):
        """测试获取 OpenAI 格式的工具列表"""
        self.registry.register(CalculatorTool())
        tools = self.registry.get_openai_tools()
        assert len(tools) == 1
        assert tools[0]["type"] == "function"


class TestRetrievalTool:
    """检索工具测试（使用 mock）"""

    def test_retrieval_tool_with_mock(self):
        """测试检索工具（mock 向量库）"""
        from src.tools.retrieval import RetrievalTool

        # 创建 mock VectorStore
        mock_store = Mock()
        mock_result = Mock()
        mock_result.text = "Apple total revenue was $416,161 million"
        mock_result.metadata = {"page": 1, "source": "FY25.pdf"}
        mock_result.score = 0.85
        mock_store.search.return_value = [mock_result]

        # 创建检索工具
        tool = RetrievalTool(vector_store=mock_store, top_k=3)

        # 测试属性
        assert tool.name == "search_report"
        assert "财务" in tool.description or "搜索" in tool.description

        # 测试执行
        result = tool.execute(query="total revenue")
        assert "416,161" in result
        assert "[1]" in result
        assert "第1页" in result

        # 验证调用
        mock_store.search.assert_called_once()

    def test_retrieval_tool_no_results(self):
        """测试无结果情况"""
        from src.tools.retrieval import RetrievalTool

        mock_store = Mock()
        mock_store.search.return_value = []

        tool = RetrievalTool(vector_store=mock_store)
        result = tool.execute(query="something not found")

        assert "未找到" in result

    def test_retrieval_tool_with_year_filter(self):
        """测试年份过滤"""
        from src.tools.retrieval import RetrievalTool

        mock_store = Mock()
        mock_store.search.return_value = []

        tool = RetrievalTool(vector_store=mock_store)
        tool.execute(query="revenue", year=2025)

        # 验证 search 被调用了（第一次带 where，第二次不带）
        assert mock_store.search.call_count >= 1


# ========== 运行测试 ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
