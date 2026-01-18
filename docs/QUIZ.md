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

## 第五部分：RAG 与 Embedding（阶段3）

### 题目 8：Embedding 向量维度

**Embedding 向量的维度（如 1536）是怎么来的？**

- A. Transformer 模型结构决定的
- B. 分词库（tokenizer）决定的
- C. OpenAI 设计模型时人为选择的
- D. GPT 输入层需要的维度

<details>
<summary>查看答案</summary>

**答案：C**

**解析**：
1536 维是 OpenAI 设计 `text-embedding-3-small` 模型时**人为选择**的，是在精度和效率之间的平衡：

| 模型 | 维度 | 特点 |
|------|------|------|
| text-embedding-3-small | 1536 | 性价比高 |
| text-embedding-3-large | 3072 | 更精确，成本更高 |

维度越高，能表达的语义细节越多，但计算和存储成本也越高。1536 = 512 × 3，这种数字便于 GPU 计算优化。

**注意**：这和 GPT 的输入维度是两回事。GPT 用的是 token embedding，Embedding API 用的是 sentence embedding。
</details>

---

### 题目 9：余弦相似度的值域

**实验中，语义不相关的两个句子（"苹果收入" vs "今天天气"）相似度是 0.15，而不是 0 或负数。为什么？**

- A. 代码有 bug
- B. 在高维空间中随机向量很难完全正交，且它们不是语义相反的关系
- C. Embedding 模型质量不好

<details>
<summary>查看答案</summary>

**答案：B**

**解析**：

**为什么不是 0？**
- 在 1536 维空间中，两个随机向量几乎不可能完全正交（夹角恰好 90°）
- 即使语义不相关，向量可能有共同的"基础特征"（都是中文、都是陈述句等）

**为什么不是负数？**
- 负数表示**语义相反**，如 "我喜欢" vs "我讨厌"
- "苹果收入" 和 "今天天气" 不是相反关系，只是**不相关**

**实际判断标准**：
- `> 0.7`：高度相关
- `0.3 ~ 0.7`：可能相关
- `< 0.3`：基本不相关
</details>

---

### 题目 10：RAG 中 LLM 的角色

**在 RAG 系统中，向量相似度比较是谁做的？**

- A. LLM 接收查询向量和知识库向量，进行比较
- B. 我们的代码用余弦相似度计算，LLM 只看到检索出的文本
- C. 向量数据库和 LLM 协作完成

<details>
<summary>查看答案</summary>

**答案：B**

**解析**：
这是理解 RAG 的**核心**！

```
用户问题 ──► Embedding ──► 向量 ──► 向量数据库搜索 ──► 相关文本片段
                                        │
                                        ▼
                              ┌──────────────────┐
                              │  构建 Prompt：    │
                              │  "根据以下内容... │
                              │   [文本片段1]    │
                              │   [文本片段2]    │
                              │   问题：xxx"     │
                              └────────┬─────────┘
                                       ▼
                                     LLM
                                       ▼
                                    最终答案
```

**关键理解**：
- ❌ 错误：把向量给 LLM 让它比较
- ✅ 正确：我们自己做向量搜索，把**文本**（不是向量）给 LLM

LLM 完全不知道向量的存在，它只看到拼接好的文本 prompt。
</details>

---

### 题目 13：Chunking 中的 Overlap（重叠）

**为什么切分时需要 overlap（重叠）？重叠带来的重复问题怎么处理？**

<details>
<summary>查看答案</summary>

**为什么需要 overlap：**
- 固定字符数切分可能在关键词中间切断
- 例如 `"毛利润"` 被切成 `"毛利"` 和 `"润"`
- overlap 让相邻块有部分重叠，即使切断也能在下一块找到完整内容

**overlap 的方向：**
```
原文: "ABCDEFGHIJ"
chunk_size=6, overlap=2

块1: [ABCDEF]     位置 0-6
块2:     [EFGHIJ]  位置 4-10 (从 6-2=4 开始)

EF 是重叠部分，在两个块中都出现
```

**重复问题的处理：**
1. 检索阶段去重：检测文本重叠，合并相邻块
2. 相似度过滤：删除高度相似的结果
3. 位置判断：相邻块只保留相似度更高的一个

**实践建议：**
- overlap = chunk_size × 10%~20%
- 少量重复比丢失信息好，LLM 能处理轻微重复
</details>

---

### 题目 15：向量数据库 vs 普通数据库

**为什么用向量数据库（ChromaDB）而不是普通数据库（MySQL）存 Embedding？**

<details>
<summary>查看答案</summary>

**核心原因：普通数据库不擅长"相似度搜索"**

| 普通数据库 | 向量数据库 |
|------------|------------|
| 擅长精确匹配 `WHERE id = 123` | 擅长相似度搜索 `找最相似的k个` |
| 索引针对等值/范围查询优化 | 索引针对向量距离计算优化（如 HNSW） |
| 1536维向量很难建有效索引 | 专门为高维向量设计 |

**向量数据库的内部优化**：
- 使用 HNSW、IVF 等专门的向量索引算法
- 可以在百万级向量中快速找到 top-k 相似
- 普通数据库做同样的事需要全表扫描，非常慢
</details>

---

### 题目 16：元数据过滤的作用

**在向量搜索时为什么要用元数据过滤（如 `year=2023`）？过滤是怎么执行的？**

<details>
<summary>查看答案</summary>

**为什么要元数据过滤：**
1. 语义搜索不是100%准确，可能返回不相关的结果
2. 结构化约束可以缩小搜索范围，提高准确度
3. 减少搜索空间，提高速度

**执行顺序（先过滤，再搜索）：**
```
步骤1: 元数据过滤（传统布尔逻辑）
  - where={"year": 2023} → 筛选出2023年的文档
  - AND/OR 就是普通布尔运算，不涉及向量

步骤2: 向量搜索（只在子集中）
  - 在过滤后的文档中计算相似度
  - 返回 top-k 最相似的
```

**关键理解**：where 条件是预过滤，向量搜索只在过滤后的子集中进行。
</details>

---

### 题目 17：生产环境的向量数据库选择

**ChromaDB 适合生产环境吗？大型项目一般用什么？**

<details>
<summary>查看答案</summary>

**ChromaDB 定位**：学习、原型、小项目

**生产环境选择**：

| 场景 | 推荐 |
|------|------|
| 云托管、不想运维 | Pinecone |
| 自建、大规模 | Milvus、Qdrant |
| 已有 PostgreSQL | pgvector 扩展 |
| 已有 Elasticsearch | ES 的 dense_vector |
| 需要混合搜索（关键词+语义） | Elasticsearch |

**PostgreSQL + pgvector 示例**：
```sql
-- 向量类型
embedding VECTOR(1536)

-- 相似度搜索
SELECT * FROM docs ORDER BY embedding <-> query_vec LIMIT 5;
```
</details>

---

### 题目 14：好的切分 vs 坏的切分

**用户问"苹果的毛利润是多少"，哪种切分更容易找到准确答案？**

- A. 块内容：`"...收入383,285百万美元。毛利"`
- B. 块内容：`"毛利润（Gross Profit）：169,148 百万美元，毛利率：44.1%"`

<details>
<summary>查看答案</summary>

**答案：B**

**解析：**

| 切分 | 问题 |
|------|------|
| A | "毛利"不完整，被截断了，Embedding 无法正确理解语义 |
| B | 完整的语义单元，包含"毛利润"关键词和具体数值 |

**好的切分标准：**
1. 语义完整 - 不在关键词/句子中间切断
2. 主题聚焦 - 一个块最好围绕一个主题
3. 大小适中 - 500-1000 字符，不要太大或太小

**这就是为什么推荐按句子/段落边界切分**，而不是简单的固定字符数切分。
</details>

---

### 题目 12：为什么文档要分页/分块加载？

**为什么不直接把整个 PDF 当作一个字符串处理，而要分页提取？**

- A. 只是为了代码好写
- B. 避免上下文过长、方便追溯来源、便于并行处理、控制检索粒度
- C. PDF 格式要求必须分页

<details>
<summary>查看答案</summary>

**答案：B**

**解析**：
分页/分块有多个好处：

**1. 避免上下文过长**
- 整个 PDF 可能有几万字，超过 LLM 上下文限制
- 分块后可以只取相关的几块

**2. 方便追溯来源**
- 每个块带有页码信息
- 可以回答"答案来自第15页"

**3. 便于并行处理**
- 多页可以同时生成 Embedding
- 提高处理速度

**4. 控制检索粒度**
- 太大的块：语义太泛，检索不精准
- 太小的块：语义不完整，缺少上下文
- 合适的块（500-2000字）：语义完整又精准

**TXT 也分"块"的原因**：
- 保持统一的数据结构
- 后续流程（Embedding、存储、检索）可以复用同一套代码
</details>

---

### 题目 11：为什么需要 RAG？

**如果不用 RAG，直接把 100 页财报全部塞进 prompt 给 LLM，会有什么问题？**

- A. 只有成本问题，其他都正常
- B. 超出上下文窗口限制、成本高、注意力分散导致回答质量下降
- C. LLM 会拒绝处理

<details>
<summary>查看答案</summary>

**答案：B**

**解析**：
直接塞全文有三大问题：

**1. 上下文窗口限制**
- GPT-4 上下文约 128K tokens（约 10 万字）
- 100 页财报可能有 20-50 万字，直接超限

**2. 注意力分散（最重要！）**
- 虽然不完全理解 Transformer 的机制，但内容太多会导致 LLM "丢失注意力"
- 学术界称之为 **"Lost in the Middle"** 问题：LLM 对开头和结尾关注度高，中间内容容易被忽略
- 无关信息太多 = 噪音，LLM 容易"迷路"

**3. 成本问题**
- API 按 token 计费
- 每次问答发送 50,000 tokens ≈ $0.50+
- RAG 只发送相关片段（2,000 tokens）≈ $0.02
- 成本可能差 25 倍！

**4. 无法精确引用**
- 直接塞全文无法知道答案来自哪一页
- RAG 的每个片段带元数据，可以标注来源

**RAG 的本质**：
> Embedding = 语义筛选器
> 把大量文档 → 筛选成少量相关片段 → 喂给 LLM
> 解决：上下文限制、注意力分散、成本高、无法引用
</details>

---

## 第六部分：Step 3.5 完整摄取流程（问答记录）

> 以下是 Step 3.5 学完后的自测问答，包含用户回答和点评。

### 题目 18：摄取流程顺序

**问题**：RAG 数据摄取的正确顺序是什么？请说出完整的流程步骤。

**用户回答**：
> 先把文档数据抽取成字符串，然后把字符串进行切分分页分块，然后添加 metainfo，再通过配置 embedding 方法，用 chromadb 把字符和转换后的向量一起存储，当后续查询的时候，直接把查询的条件根据 metainfo 筛选，然后用 embedding 把查询量化，比较距离返回答案。

**点评**：满分！完整覆盖了整个流程，还提到了查询时的流程，理解很透彻。

```
PDF → 抽取字符串 → 切分分块 → 添加 metainfo → ChromaDB 存储(字符+向量)
                                                        ↓
                              查询时：metainfo 筛选 → embedding 量化 → 比较距离
```

---

### 题目 19：切分数量估算

**问题**：实验中，4 页 PDF 切分后得到了 4 个 chunk。如果换成一个 100 页、每页 3000 字符的财报，使用 chunk_size=800，大概会产生多少个 chunk？

**用户回答**：
> 每页会产生大概 4-6 个块，因为是通过对块的边界添加 overlap，尽可能使得切分块时不丢失太多语义联系信息，我猜大概会在 400-600 之间。

**点评**：思路正确！overlap 确实会增加块数。

精确计算：
- 100 页 × 3000 字符 = 300,000 字符
- 每页 3000 / 800 ≈ 3-4 块（不是 4-6）
- 总计约 300-400 块

估算略高，但**理解 overlap 会增加块数**这个关键点是对的。

---

### 题目 20：元数据传递

**问题**：在检索结果中，我们能看到 `result.metadata = {"page": 2}`。这个页码信息是怎么从原始 PDF 一路传递到检索结果的？

**用户回答**：
> 页码在我们把 pdf 转换为 str 分页的时候，通过自动化的方式打上标签，然后对每页下面的内容再分块，使得每页下面的块都有相同的页码，然后通过把 str 传入 chromadb，保留 metainfo 的时候，页码就被加入了。

**点评**：完全正确！准确描述了传递链：

```
PDF 分页提取 → 每页打上 page_num 标签
      ↓
切分时继承 → 每个 chunk 带有 page 信息
      ↓
存储时保留 → ChromaDB 把 metadata 和文本一起存
      ↓
检索时返回 → result.metadata["page"]
```

---

### 题目 21：自动 Embedding

**问题**：为什么调用 `store.add_documents(texts)` 时我们不需要手动调用 `embedder.embed()` 生成向量？ChromaDB 是怎么处理的？

**用户回答**：
> chromadb 内置了 api，把我们传入的分好块的字符串自动做变换，然后同时存储 str 和向量，具体是并行的调用还是怎么样我不是很清楚。

**点评**：理解正确！

关键点抓住了：ChromaDB 通过配置的 `embedding_function` 自动处理，用户不需要手动调用。

```python
# 创建集合时配置 embedding_function
collection = client.get_or_create_collection(
    embedding_function=openai_ef  # ← 这里配置好了
)

# 之后 add/query 都自动调用，用户不用管
collection.add(documents=["文本"])  # 内部自动: openai_ef(["文本"])
```

至于是并行还是串行，这是 ChromaDB 内部实现细节，不影响理解。

---

### 题目 22：跨语言检索

**问题**：实验中，中文查询"资产负债表"成功匹配到了英文内容"BALANCE SHEETS"，相似度 0.43。这说明了什么？0.43 这个分数意味着什么？

**用户回答**：
> 查询到了资产负债表的向量化的语义，0.43 是 1-cos 余弦距离得到的结果，代表这个 item 在逻辑上的相似性，资产负债表和 balance sheet 在逻辑上很相似，所以被找到了，不过由于可能英文句子比较长，所以 balance sheet 这句话的得分不太高。

**点评**：理解到位！

| 回答要点 | 评价 |
|---------|------|
| "向量化的语义" | ✓ 语义级别匹配 |
| "0.43 是 1 - cos距离" | ✓ 准确！ |
| "英文句子比较长，得分不太高" | ✓ chunk 包含整页内容，不只是标题 |

0.43 在实际应用中属于"相关"范围（0.3-0.7），可以作为可信结果返回给 LLM。

---

### Step 3.5 总评

| 问题 | 得分 |
|------|------|
| 问题 1：摄取流程 | ⭐⭐⭐⭐⭐ |
| 问题 2：切分数量 | ⭐⭐⭐⭐ |
| 问题 3：元数据传递 | ⭐⭐⭐⭐⭐ |
| 问题 4：自动 Embedding | ⭐⭐⭐⭐⭐ |
| 问题 5：跨语言检索 | ⭐⭐⭐⭐⭐ |

**Step 3.5 完全通过！**

---

## 学习检验标准

如果你能：
- [ ] 不看代码，画出函数调用流程图
- [ ] 解释 description 为什么重要
- [ ] 说清楚 messages 的累积机制
- [ ] 写出 ReAct 循环的伪代码
- [ ] 画出 RAG 的完整数据流（用户问题 → Embedding → 向量搜索 → 文本拼接 → LLM → 答案）
- [ ] 解释为什么 LLM 看不到向量，只看到文本
- [ ] **画出完整的摄取流程图（PDF → 加载 → 切分 → Embedding → 存储）**
- [ ] **解释元数据如何贯穿整个 RAG 流程**

那么你已经**真正理解** Agent 的核心原理了！
