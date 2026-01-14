# Agent 学习自测题

> 通过这些题目检验你对 Agent 核心概念的理解。
> 建议：先不看答案，自己思考后再对照解析。

---

## 第一部分：核心概念速查

### 1. Agent 的本质

```
Agent = LLM + 工具调用 + 循环决策
```

| 普通 Chatbot | Agent |
|-------------|-------|
| 一问一答 | 多轮推理 |
| 只靠模型知识 | 能调用外部工具 |
| 输入→输出 | 输入→思考→行动→观察→...→输出 |

### 2. 函数调用流程（5步）

```
1. 定义工具 (JSON Schema)
      ↓
2. 调用 LLM (带上工具定义)
      ↓
3. LLM 返回工具调用指令 (不是执行！)
      ↓
4. 我们执行工具，获取结果
      ↓
5. 把结果喂回 LLM，生成最终答案
```

### 3. ReAct 模式

```
ReAct = Reasoning + Acting

循环：思考(Thought) → 行动(Action) → 观察(Observation) → 思考 → ...
```

### 4. messages 机制

```python
messages = []
messages.append(...)  # 只是往列表加数据，不发送！
messages.append(...)  # 还是不发送！

# 只有这里才真正发送整个列表
response = client.chat.completions.create(messages=messages)
```

---

## 第二部分：自测题目

### 题目 1：工具执行

**LLM 调用工具时，谁负责真正执行工具代码？**

- A. LLM 自己执行 Python 代码
- B. OpenAI 服务器执行
- C. 我们的代码解析指令并执行

<details>
<summary>查看答案</summary>

**答案：C**

**解析**：
LLM 不能执行代码！它只是返回一个"指令"，告诉你要调用什么函数、传什么参数：

```python
# LLM 返回的只是指令
tool_calls = [
    {"function": {"name": "calculator", "arguments": '{"expression": "1+1"}'}}
]

# 我们负责执行
result = calculator(expression="1+1")  # 我们写的代码执行这个
```

这是 Agent 架构的核心：**LLM 负责决策，我们负责执行**。
</details>

---

### 题目 2：工具描述

**Tool 的 `description` 属性有什么作用？**

- A. 给人类开发者看的注释
- B. LLM 靠它决定何时调用这个工具
- C. 可选字段，不写也行

<details>
<summary>查看答案</summary>

**答案：B**

**解析**：
`description` 是**最重要**的字段！LLM 完全靠这个描述来判断：
1. 这个工具能做什么
2. 什么时候应该使用它

```python
# 好的描述
description = "执行数学计算，如加减乘除、百分比、增长率。输入表达式如 '100*0.15'"

# 差的描述
description = "计算器"  # 太模糊，LLM 不知道什么时候该用
```

**面试要点**：如果面试官问"怎么让 LLM 正确调用工具"，一定要提到 description 的重要性。
</details>

---

### 题目 3：ReAct 循环终止

**ReAct 循环什么时候结束？**

- A. 固定循环 10 次
- B. 当 LLM 不再返回 tool_calls 时
- C. 用户手动输入停止命令

<details>
<summary>查看答案</summary>

**答案：B（以及达到最大迭代次数时）**

**解析**：
有两个终止条件：

```python
for i in range(max_iterations):        # 条件1: 达到最大次数（防死循环）
    response = llm.call(messages)

    if response.tool_calls:
        # 有工具调用，继续循环
        execute_tools()
    else:
        # 条件2: 没有工具调用 = LLM 准备好回答了
        return response.content        # 终止循环
```

**关键理解**：LLM 自己决定什么时候"够了"。当它认为信息足够回答问题时，就不再调用工具。
</details>

---

### 题目 4：并行工具调用

**在测试中，第1轮 LLM 同时调用了 `search(2023)` 和 `search(2022)`。这是怎么实现的？**

- A. 发了两次 API 请求，每次调用一个工具
- B. LLM 一次返回多个 tool_calls，我们遍历执行
- C. 工具框架自动检测并并行执行

<details>
<summary>查看答案</summary>

**答案：B**

**解析**：
`tool_calls` 是一个**列表**，LLM 可以一次返回多个工具调用：

```python
# LLM 返回的结构
response.tool_calls = [
    {"id": "call_1", "function": {"name": "search", "arguments": '{"year": 2023}'}},
    {"id": "call_2", "function": {"name": "search", "arguments": '{"year": 2022}'}}
]

# 我们遍历执行每一个
for tool_call in response.tool_calls:
    result = execute(tool_call)
    messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
```

**注意**：虽然 LLM 一次返回多个，但我们的代码是顺序执行的。如果要真正并行，需要用 `asyncio` 或线程池。
</details>

---

### 题目 5：消息发送机制

**`messages.append()` 会发送 API 请求吗？**

- A. 会，每次 append 都会发送
- B. 不会，只有调用 `create()` 时才发送整个列表

<details>
<summary>查看答案</summary>

**答案：B**

**解析**：
`messages` 就是一个普通的 Python 列表，`append()` 只是往列表里加元素：

```python
messages = []
messages.append({"role": "user", "content": "你好"})      # 不发送
messages.append({"role": "tool", "content": "结果"})      # 不发送
messages.append({"role": "tool", "content": "结果2"})     # 不发送

# 只有这里才发送！而且发送的是整个列表
response = client.chat.completions.create(messages=messages)
```

**这就是为什么 LLM 能"记住"之前的对话**——每次都把完整历史发过去。
</details>

---

### 题目 6：工具定义格式

**OpenAI 工具定义使用什么格式描述参数？**

- A. Python 类型注解
- B. JSON Schema
- C. XML

<details>
<summary>查看答案</summary>

**答案：B**

**解析**：
工具参数使用 JSON Schema 格式定义：

```python
{
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "执行数学计算",
        "parameters": {                    # JSON Schema 格式
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",      # 参数类型
                    "description": "数学表达式"
                }
            },
            "required": ["expression"]     # 必填参数
        }
    }
}
```

JSON Schema 是一个标准规范，用于描述 JSON 数据的结构。
</details>

---

### 题目 7：防止死循环

**如何防止 Agent 陷入无限循环？**

- A. 设置 `max_iterations` 限制最大迭代次数
- B. 在 System Prompt 中指示"不要重复调用相同工具"
- C. 记录已调用的工具，避免重复
- D. 以上都是

<details>
<summary>查看答案</summary>

**答案：D**

**解析**：
防止死循环需要多重保护：

```python
# 方法1: 硬性限制
max_iterations = 10

# 方法2: Prompt 约束
system_prompt = """
重要规则：
- 如果连续3次搜索找不到，直接告诉用户
- 不要重复调用相同的工具和参数
"""

# 方法3: 代码层面检测
called = set()
if (tool_name, args) in called:
    break  # 跳过重复调用
called.add((tool_name, args))
```
</details>

---

## 第三部分：代码关键点速查

### base.py - 工具基类

```python
class Tool(ABC):
    @property
    def name(self) -> str: ...        # 工具名称
    @property
    def description(self) -> str: ... # 工具描述（最重要！）
    @property
    def parameters(self) -> dict: ... # 参数定义（JSON Schema）

    def execute(self, **kwargs) -> str: ...  # 执行逻辑
    def to_openai_tool(self) -> dict: ...    # 转换为 API 格式
```

### calculator.py - 具体工具实现

```python
class CalculatorTool(Tool):
    name = "calculator"
    description = "执行数学计算..."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式"}
        },
        "required": ["expression"]
    }

    def execute(self, expression: str) -> str:
        return str(eval(expression))
```

### simple_agent.py - 单次工具调用

```python
# 1. 调用 LLM
response = client.chat.completions.create(messages=messages, tools=tools)

# 2. 检查是否调用工具
if response.tool_calls:
    # 3. 执行工具
    result = execute_tool(response.tool_calls[0])
    # 4. 喂回结果
    messages.append({"role": "tool", "content": result})
    # 5. 再次调用获取最终答案
    final = client.chat.completions.create(messages=messages)
```

### orchestrator.py - ReAct 循环

```python
for i in range(max_iterations):
    response = client.chat.completions.create(messages=messages, tools=tools)

    if response.tool_calls:
        messages.append(response.message)
        for tool_call in response.tool_calls:
            result = execute(tool_call)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
        # 继续循环
    else:
        return response.content  # 结束循环
```

---

## 第四部分：面试高频问题

### Q1: 介绍一下你的 Agent 架构？

**答题要点**：
1. 画图：用户输入 → 意图识别 → ReAct循环(工具调用) → 答案生成
2. 核心是 ReAct 模式：思考-行动-观察循环
3. 工具包括：检索、计算、表格抽取
4. 防幻觉：基于证据回答，带引用

### Q2: 函数调用是怎么工作的？

**答题要点**：
1. JSON Schema 定义工具
2. LLM 返回工具名+参数（不执行）
3. 我们执行工具，结果加入对话
4. 再次调用 LLM 生成答案

### Q3: 如何防止 Agent 幻觉？

**答题要点**：
1. System Prompt 要求"没证据就说不知道"
2. 数值计算用工具，不让 LLM 心算
3. 每个结论带引用来源
4. 检索为空时返回"需要更多信息"

### Q4: ReAct 和普通 Chain 有什么区别？

**答题要点**：
- Chain：固定流程，A→B→C
- ReAct：动态决策，LLM 自己决定下一步做什么
- ReAct 更灵活，能处理复杂多变的任务

---

## 学习检验标准

如果你能：
- [ ] 不看代码，画出函数调用流程图
- [ ] 解释 description 为什么重要
- [ ] 说清楚 messages 的累积机制
- [ ] 写出 ReAct 循环的伪代码

那么你已经**真正理解** Agent 的核心原理了！
