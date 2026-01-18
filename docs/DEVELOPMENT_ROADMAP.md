# 开发路线图 (Development Roadmap)

> 本文档记录项目的开发计划和进度，每完成一步请更新对应的 checkbox。

---

## 进度总览

| 阶段 | 内容 | 状态 |
|------|------|------|
| 阶段 1-2 | 基础 Agent (Tool Use + ReAct) | ✅ 已完成 |
| 阶段 3 | RAG 集成 | ✅ 已完成 |
| 阶段 4 | 完善功能 | 🚧 进行中 |

---

## 阶段 3: RAG 集成

### Step 3.1: Embedding 基础实验
- [x] **完成** ✅

**目标**: 理解文本如何变成向量，体验语义相似度

**动手实验** `experiments/01_embedding_basics.py`:
```python
# 实验内容：
# 1. 调用 OpenAI embedding API，把一句话变成向量
# 2. 观察向量的维度（1536维）
# 3. 计算两个句子的余弦相似度
# 4. 对比实验：
#    - "苹果2023年收入是3832亿" vs "Apple revenue in 2023 was 383B" → 高相似度
#    - "苹果2023年收入是3832亿" vs "今天天气很好" → 低相似度
```

**产出**: `src/index/embedder.py`

**学到的知识点**:
- Embedding 将文本转换为 1536 维向量（text-embedding-3-small 模型）
- 余弦相似度范围 [-1, 1]，越接近 1 表示越相似
- 语义相似的句子（即使不同语言）相似度高（中英文相似句 0.78）
- 语义不相关的句子相似度低（0.15）
- 这是向量检索（RAG）的基础原理

---

### Step 3.2: PDF 文档加载
- [x] **完成** ✅

**目标**: 把 PDF 变成纯文本

**动手实验** `experiments/02_pdf_loading.py`:
```python
# 实验内容：
# 1. 用 PyMuPDF 打开 PDF
# 2. 逐页提取文本
# 3. 观察表格、图片说明的提取效果
# 4. 提取元数据（页码、标题）
```

**产出**: `src/ingestion/loader.py`

**学到的知识点**:
- PyMuPDF (fitz) 可快速提取 PDF 文本，支持逐页处理
- 按页提取便于后续标注来源（"答案来自第X页"）
- 设计了 Document 和 Page 数据类，统一不同格式的处理
- TXT 文件可按章节分割模拟"页面"结构，保持接口一致

---

### Step 3.3: 文档切分 Chunking
- [x] **完成** ✅

**目标**: 理解切分策略，选择合适的 chunk_size 和 overlap

**动手实验** `experiments/03_chunking.py`:
```python
# 实验内容：
# 1. 固定字符数切分（500字）→ 观察句子被切断问题
# 2. 加入 overlap（重叠）→ 观察改善效果
# 3. 按段落/句子边界切分 → 对比效果
# 4. 统计 token 数

# 参数实验：
# - chunk_size: 300 vs 500 vs 1000
# - overlap: 0 vs 50 vs 100
```

**产出**: `src/ingestion/chunker.py`

**学到的知识点**:
- 固定字符数切分会在关键词中间切断（如"毛利润"→"毛利"+"润"）
- overlap（重叠）通过让相邻块有部分重叠来减少信息丢失
- 按句子/段落边界切分保持语义完整，是推荐策略
- 推荐参数：chunk_size=500-1000，overlap=10%-20%
- 太大的块语义太泛，太小的块语义不完整，需要平衡

---

### Step 3.4: 向量数据库入门
- [x] **完成** ✅

**目标**: 掌握 ChromaDB 的基本操作

**动手实验** `experiments/04_vector_store.py`:
```python
# 实验内容：
# 1. 创建 ChromaDB 集合
# 2. 插入文本 + 向量 + 元数据
# 3. 查询 top-k 相似结果
# 4. 元数据过滤（如：只搜 2023 年）

# 示例数据：
# doc1: "2023年毛利率44.1%"  {year: 2023, topic: "毛利率"}
# doc2: "2022年毛利率43.3%"  {year: 2022, topic: "毛利率"}
# doc3: "2023年收入3832亿"   {year: 2023, topic: "收入"}

# 查询: "苹果的毛利率是多少" → 应返回 doc1, doc2
```

**产出**: `src/index/vector_store.py`

**学到的知识点**:
- ChromaDB 自动处理 Embedding，只需传文本
- 元数据过滤是"先过滤，再搜索"，AND/OR 是布尔逻辑，不涉及向量
- 返回的是"距离"，可转换为相似度（1-distance）
- ChromaDB 适合学习/小项目，生产环境考虑 Pinecone/Milvus/pgvector
- 元数据过滤可缩小搜索范围，提高准确度和速度

---

### Step 3.5: 完整摄取流程
- [x] **完成** ✅

**目标**: 串联 加载 → 切分 → Embedding → 存储

**动手实验** `experiments/05_full_ingestion.py`:
```python
# 完整流程：
# 1. 加载 PDF 财报文档
# 2. 切分成 chunks（按页 + 段落边界）
# 3. 自动生成 embeddings（ChromaDB 内部处理）
# 4. 存入 ChromaDB（文本 + 向量 + 元数据）
# 5. 测试检索效果（语义搜索 + 元数据过滤）
```

**产出**: `experiments/05_full_ingestion.py`

**学到的知识点**:
- 完整流程：PDF → DocumentLoader → Chunker → VectorStore
- ChromaDB 自动处理 Embedding，只需传入文本
- 元数据（页码、来源）贯穿整个流程，检索时一起返回
- 中文查询能匹配英文财报内容（跨语言语义搜索）
- 相似度 0.4-0.7 属于"相关"范围，可作为可信结果

---

### Step 3.6: 检索工具实现
- [x] **完成** ✅

**目标**: 将检索封装成 Agent 可调用的工具

**动手实验** `experiments/06_rag_agent.py`:
```python
# 实验内容：
# 1. 创建 RetrievalTool 继承 Tool 基类
# 2. 定义参数：query, year(可选)
# 3. execute() 调用 VectorStore.search() 进行语义检索
# 4. 返回格式化结果（带来源页码）
# 5. 与 AgentOrchestrator 集成，实现完整问答
```

**产出**: `src/tools/retrieval.py`

**学到的知识点**:
- RetrievalTool 通过依赖注入接收 VectorStore 实例
- Tool 的 description 决定 LLM 何时调用该工具
- 检索结果需要格式化，包含来源信息方便 LLM 引用
- 元数据过滤失败时可回退到无过滤搜索

---

### Step 3.7: 集成测试
- [x] **完成** ✅

**目标**: 端到端验证 Agent + RAG

**测试内容**:
```python
# 1. 加载 PDF 财报到向量数据库
# 2. 创建 Agent，注册 RetrievalTool + CalculatorTool
# 3. 测试问题："苹果公司2025财年的总净销售额是多少？"
# 4. 验证 Agent 正确检索并回答：$416,161 million ✓
```

**产出**: `experiments/06_rag_agent.py`

**学到的知识点**:
- RAG 成功接入 Agent 的 ReAct 循环
- Agent 自动决定何时调用检索工具、何时直接回答
- 真实语义检索替代了之前的 MockSearchTool
- 中文问题可以检索英文财报并正确回答

---

## 阶段 4: 完善功能

### Step 4.1: 答案生成优化
- [ ] **完成**

- 添加引用标注（来源页码）
- 格式化输出结构

**产出**: `src/synthesis/answer.py`

---

### Step 4.2: CLI 交互
- [ ] **完成**

- 多轮对话支持
- 会话保存/加载

**产出**: `src/interface/cli.py`, `src/interface/session.py`

---

### Step 4.3: 测试用例
- [ ] **完成**

- 各工具单元测试
- 端到端测试

**产出**: `tests/test_*.py`

---

## 文件结构预览

```
experiments/                    # 独立实验脚本
├── 01_embedding_basics.py     # Step 3.1 - Embedding 基础
├── 02_pdf_loading.py          # Step 3.2 - PDF 加载
├── 03_chunking.py             # Step 3.3 - 文档切分
├── 04_vector_store.py         # Step 3.4 - 向量数据库
├── 05_full_ingestion.py       # Step 3.5 - 完整摄取流程
└── 06_rag_agent.py            # Step 3.6/3.7 - RAG Agent 完整演示

src/
├── index/
│   ├── embedder.py            # Step 3.1 产出
│   └── vector_store.py        # Step 3.4 产出
├── ingestion/
│   ├── loader.py              # Step 3.2 产出
│   └── chunker.py             # Step 3.3 产出
└── tools/
    ├── base.py                # 工具基类
    ├── calculator.py          # 计算器工具
    └── retrieval.py           # Step 3.6 产出 - 检索工具
```

---

## 当前位置

**已完成**: 阶段 3 - RAG 集成（全部完成）

**正在进行**: 阶段 4 - 完善功能

**下一步**: Step 4.1 - 答案生成优化（添加引用标注、格式化输出）
