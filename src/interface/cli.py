"""
CLI 交互模块 - Command Line Interface

功能：
====
带命令的 REPL 风格交互：
- 直接输入问题进行问答
- /help    - 显示帮助
- /load    - 加载 PDF 文档
- /docs    - 查看已加载的文档
- /save    - 保存会话
- /history - 查看对话历史
- /clear   - 清除对话历史
- /exit    - 退出

运行方式：
========
python -m src.interface.cli
"""

import os
import sys

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from src.interface.session import Session, SessionManager
from src.ingestion.loader import DocumentLoader
from src.ingestion.chunker import Chunker
from src.index.vector_store import VectorStore
from src.tools.retrieval import RetrievalTool
from src.tools.calculator import CalculatorTool
from src.agent.orchestrator import AgentOrchestrator


class CLI:
    """
    命令行交互界面

    REPL 循环：
    1. 读取用户输入
    2. 判断是命令还是问题
    3. 执行命令或调用 Agent
    4. 显示结果
    """

    # 命令前缀
    COMMAND_PREFIX = "/"

    # 帮助信息
    HELP_TEXT = """
可用命令：
  /help           显示此帮助信息
  /load <路径>    加载 PDF 文档到知识库
  /docs           查看已加载的文档
  /save [名称]    保存当前会话
  /list           列出已保存的会话
  /restore <名称> 恢复会话
  /history        查看对话历史
  /clear          清除对话历史
  /exit           退出程序

直接输入问题即可进行问答。
"""

    def __init__(self):
        """初始化 CLI"""
        self.session = Session()
        self.session_manager = SessionManager()

        # 向量存储（延迟初始化）
        self.vector_store = None

        # Agent（延迟初始化）
        self.agent = None

        # 文档处理工具
        self.loader = DocumentLoader()
        self.chunker = Chunker(chunk_size=800, overlap=100, min_chunk_size=100)

    def _init_vector_store(self):
        """初始化向量存储"""
        if self.vector_store is None:
            self.vector_store = VectorStore(
                collection_name=self.session.collection_name,
                persist_directory=None  # 内存存储
            )

    def _init_agent(self):
        """初始化 Agent"""
        if self.agent is None:
            self._init_vector_store()

            self.agent = AgentOrchestrator(
                model="gpt-4o-mini",
                max_iterations=10,
                verbose=False  # CLI 模式下关闭详细日志
            )

            # 注册工具
            retrieval_tool = RetrievalTool(
                vector_store=self.vector_store,
                top_k=3,
                min_score=0.0
            )
            self.agent.register_tool(retrieval_tool)
            self.agent.register_tool(CalculatorTool())

    def _print(self, text: str, prefix: str = ""):
        """打印输出"""
        if prefix:
            print(f"{prefix} {text}")
        else:
            print(text)

    def _print_error(self, text: str):
        """打印错误"""
        print(f"[错误] {text}")

    def _print_success(self, text: str):
        """打印成功"""
        print(f"[OK] {text}")

    def _print_info(self, text: str):
        """打印信息"""
        print(f"[信息] {text}")

    # ========== 命令处理 ==========

    def cmd_help(self, args: list[str]):
        """显示帮助"""
        print(self.HELP_TEXT)

    def cmd_load(self, args: list[str]):
        """加载文档"""
        if not args:
            self._print_error("请指定文档路径，例如: /load data/report.pdf")
            return

        path = " ".join(args)

        # 检查文件是否存在
        if not os.path.exists(path):
            self._print_error(f"文件不存在: {path}")
            return

        try:
            self._print_info(f"正在加载: {path}")

            # 加载文档
            document = self.loader.load(path)
            self._print_info(f"页数: {document.page_count}, 字符数: {document.total_chars:,}")

            # 切分
            all_chunks = []
            for page in document.pages:
                page_metadata = {
                    "source": os.path.basename(document.source),
                    "page": page.page_num,
                }
                chunks = self.chunker.split(page.text, metadata=page_metadata)
                all_chunks.extend(chunks)

            self._print_info(f"切分成 {len(all_chunks)} 个文本块")

            # 存入向量数据库
            self._init_vector_store()
            texts = [chunk.text for chunk in all_chunks]
            metadatas = [chunk.metadata for chunk in all_chunks]
            self.vector_store.add_documents(texts=texts, metadatas=metadatas)

            # 记录到会话
            self.session.add_document(path)

            # 重新初始化 Agent（使用更新后的向量库）
            self.agent = None
            self._init_agent()

            self._print_success(f"文档加载完成，共 {self.vector_store.count} 条记录")

        except Exception as e:
            self._print_error(f"加载失败: {e}")

    def cmd_docs(self, args: list[str]):
        """查看已加载的文档"""
        if not self.session.loaded_documents:
            self._print_info("尚未加载任何文档")
            return

        print("\n已加载的文档：")
        for i, doc in enumerate(self.session.loaded_documents, 1):
            print(f"  {i}. {doc}")

        if self.vector_store:
            print(f"\n向量库记录数: {self.vector_store.count}")

    def cmd_save(self, args: list[str]):
        """保存会话"""
        name = args[0] if args else None

        try:
            path = self.session_manager.save(self.session, name)
            self._print_success(f"会话已保存: {path}")
        except Exception as e:
            self._print_error(f"保存失败: {e}")

    def cmd_list(self, args: list[str]):
        """列出已保存的会话"""
        sessions = self.session_manager.list_sessions()

        if not sessions:
            self._print_info("没有已保存的会话")
            return

        print("\n已保存的会话：")
        for s in sessions:
            docs_info = f", {len(s['documents'])} 个文档" if s['documents'] else ""
            print(f"  {s['name']}: {s['message_count']} 条消息{docs_info}")

    def cmd_restore(self, args: list[str]):
        """恢复会话"""
        if not args:
            self._print_error("请指定会话名称，例如: /restore my_session")
            return

        name = args[0]
        loaded = self.session_manager.load(name)

        if loaded is None:
            self._print_error(f"会话不存在: {name}")
            return

        self.session = loaded
        self._print_success(f"会话已恢复: {len(self.session.messages)} 条消息")

        # 重新加载文档
        if self.session.loaded_documents:
            self._print_info("正在重新加载文档...")
            for doc_path in self.session.loaded_documents:
                if os.path.exists(doc_path):
                    self.cmd_load([doc_path])
                else:
                    self._print_error(f"文档不存在: {doc_path}")

    def cmd_history(self, args: list[str]):
        """查看对话历史"""
        if not self.session.messages:
            self._print_info("对话历史为空")
            return

        print("\n对话历史：")
        print("-" * 50)
        for msg in self.session.messages:
            role = "你" if msg["role"] == "user" else "助手"
            content = msg["content"]
            # 截断长内容
            if len(content) > 200:
                content = content[:200] + "..."
            print(f"[{role}] {content}\n")

    def cmd_clear(self, args: list[str]):
        """清除对话历史"""
        self.session.clear_messages()
        self._print_success("对话历史已清除")

    def cmd_exit(self, args: list[str]):
        """退出"""
        print("\n再见！")
        sys.exit(0)

    # ========== 主循环 ==========

    def handle_command(self, line: str) -> bool:
        """
        处理命令

        返回：
            True 如果是命令，False 如果是普通问题
        """
        if not line.startswith(self.COMMAND_PREFIX):
            return False

        # 解析命令和参数
        parts = line[1:].split()
        if not parts:
            return True

        cmd = parts[0].lower()
        args = parts[1:]

        # 命令映射
        commands = {
            "help": self.cmd_help,
            "load": self.cmd_load,
            "docs": self.cmd_docs,
            "save": self.cmd_save,
            "list": self.cmd_list,
            "restore": self.cmd_restore,
            "history": self.cmd_history,
            "clear": self.cmd_clear,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
            "q": self.cmd_exit,
        }

        if cmd in commands:
            commands[cmd](args)
        else:
            self._print_error(f"未知命令: /{cmd}，输入 /help 查看帮助")

        return True

    def handle_question(self, question: str):
        """处理问题"""
        # 检查是否加载了文档
        if not self.session.loaded_documents:
            self._print_info("提示: 尚未加载文档，请先使用 /load 加载 PDF")
            self._print_info("示例: /load data/FY25_Q4_Consolidated_Financial_Statements.pdf")
            return

        # 初始化 Agent
        self._init_agent()

        # 记录问题
        self.session.add_message("user", question)

        try:
            # 调用 Agent
            print("\n思考中...\n")
            answer = self.agent.run(question)

            # 记录回答
            self.session.add_message("assistant", answer)

            # 显示回答
            print("\n" + "=" * 50)
            print("回答：")
            print("=" * 50)
            print(answer)
            print("=" * 50 + "\n")

        except Exception as e:
            self._print_error(f"处理失败: {e}")

    def run(self):
        """运行 REPL 循环"""
        # 检查 API Key
        if not os.getenv("OPENAI_API_KEY"):
            self._print_error("请在 .env 文件中设置 OPENAI_API_KEY")
            return

        # 欢迎信息
        print("\n" + "=" * 50)
        print("财报分析助手")
        print("=" * 50)
        print("输入问题进行问答，或输入 /help 查看命令")
        print("=" * 50 + "\n")

        # REPL 循环
        while True:
            try:
                # 读取输入
                line = input("> ").strip()

                if not line:
                    continue

                # 判断是命令还是问题
                if self.handle_command(line):
                    continue

                # 处理问题
                self.handle_question(line)

            except KeyboardInterrupt:
                print("\n\n使用 /exit 退出")
            except EOFError:
                break


# ========== 入口 ==========

def main():
    """程序入口"""
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()
