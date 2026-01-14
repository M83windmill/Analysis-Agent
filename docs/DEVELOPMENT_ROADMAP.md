# 开发路线图 (Development Roadmap)

> 本文档记录项目的开发计划和进度，每完成一步请更新对应的 checkbox。

---

## 进度总览

| 阶段 | 内容 | 状态 |
|------|------|------|
| 阶段 1-2 | 基础 Agent (Tool Use + ReAct) | ✅ 已完成 |
| 阶段 3 | RAG 集成 | 🚧 进行中 |
| 阶段 4 | 完善功能 | ⏳ 待开始 |

---

## 阶段 3: RAG 集成

### Step 3.1: Embedding 基础实验
- [ ] **完成**

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
- _（完成后记录）_

---

### Step 3.2: PDF 文档加载
- [ ] **完成**

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
- _（完成后记录）_

---

### Step 3.3: 文档切分 Chunking
- [ ] **完成**

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
- _（完成后记录）_

---

### Step 3.4: 向量数据库入门
- [ ] **完成**

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
- _（完成后记录）_

---

### Step 3.5: 完整摄取流程
- [ ] **完成**

**目标**: 串联 加载 → 切分 → Embedding → 存储

**动手实验** `experiments/05_full_ingestion.py`:
```python
# 完整流程：
# 1. 加载 data/sample_report.txt
# 2. 切分成 chunks
# 3. 生成 embeddings
# 4. 存入 ChromaDB
# 5. 测试检索效果
```

**产出**: 各模块整合验证

**学到的知识点**:
- _（完成后记录）_

---

### Step 3.6: 检索工具实现
- [ ] **完成**

**目标**: 将检索封装成 Agent 可调用的工具

**动手实验** `experiments/06_retrieval_tool.py`:
```python
# 实验内容：
# 1. 创建 RetrievalTool 继承 Tool 基类
# 2. 定义参数：query, year(可选), top_k
# 3. execute() 调用向量库检索
# 4. 返回格式化结果（带来源标注）
```

**产出**: `src/tools/retrieval.py`（替换 MockSearchTool）

**学到的知识点**:
- _（完成后记录）_

---

### Step 3.7: 集成测试
- [ ] **完成**

**目标**: 端到端验证 Agent + RAG

**测试内容**:
```python
# 1. 用 RetrievalTool 替换 MockSearchTool
# 2. 测试问题："苹果2023年毛利率比2022年提高了多少？"
# 3. 验证 Agent 能正确检索 + 计算
```

**产出**: 更新 `src/agent/orchestrator.py`

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
├── 01_embedding_basics.py
├── 02_pdf_loading.py
├── 03_chunking.py
├── 04_vector_store.py
├── 05_full_ingestion.py
└── 06_retrieval_tool.py

src/
├── index/
│   ├── embedder.py            # Step 3.1 产出
│   └── vector_store.py        # Step 3.4 产出
├── ingestion/
│   ├── loader.py              # Step 3.2 产出
│   └── chunker.py             # Step 3.3 产出
└── tools/
    └── retrieval.py           # Step 3.6 产出
```

---

## 当前位置

**正在进行**: Step 3.1 - Embedding 基础实验

**下一步**: 创建 `experiments/01_embedding_basics.py` 并运行实验
