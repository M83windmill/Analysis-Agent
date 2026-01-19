"""
会话管理模块 - Session Manager

功能：
====
1. 保存对话历史到文件
2. 从文件加载对话历史
3. 管理会话元数据（创建时间、文档来源等）

文件格式：JSON
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Session:
    """
    会话数据

    包含：
    - 对话历史
    - 加载的文档信息
    - 元数据
    """
    # 对话历史：[{"role": "user", "content": "..."}, ...]
    messages: list[dict] = field(default_factory=list)

    # 已加载的文档路径
    loaded_documents: list[str] = field(default_factory=list)

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # 向量数据库集合名（用于恢复时重建检索）
    collection_name: str = "financial_reports"

    def add_message(self, role: str, content: str):
        """添加消息到历史"""
        self.messages.append({"role": role, "content": content})
        self.updated_at = datetime.now().isoformat()

    def add_document(self, doc_path: str):
        """记录已加载的文档"""
        if doc_path not in self.loaded_documents:
            self.loaded_documents.append(doc_path)
            self.updated_at = datetime.now().isoformat()

    def clear_messages(self):
        """清除对话历史（保留文档信息）"""
        self.messages = []
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """转为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """从字典创建"""
        return cls(
            messages=data.get("messages", []),
            loaded_documents=data.get("loaded_documents", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            collection_name=data.get("collection_name", "financial_reports")
        )


class SessionManager:
    """
    会话管理器

    负责：
    - 保存会话到 JSON 文件
    - 加载会话从 JSON 文件
    - 列出可用的会话
    """

    def __init__(self, sessions_dir: str = "./sessions"):
        """
        初始化

        参数：
            sessions_dir: 会话文件保存目录
        """
        self.sessions_dir = sessions_dir
        self._ensure_dir()

    def _ensure_dir(self):
        """确保目录存在"""
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)

    def save(self, session: Session, name: str = None) -> str:
        """
        保存会话

        参数：
            session: 会话对象
            name: 文件名（不含扩展名），默认用时间戳

        返回：
            保存的文件路径
        """
        if name is None:
            name = datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"{name}.json"
        filepath = os.path.join(self.sessions_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)

        return filepath

    def load(self, name: str) -> Optional[Session]:
        """
        加载会话

        参数：
            name: 文件名（可带或不带 .json 扩展名）

        返回：
            Session 对象，如果文件不存在返回 None
        """
        if not name.endswith(".json"):
            name = f"{name}.json"

        filepath = os.path.join(self.sessions_dir, name)

        if not os.path.exists(filepath):
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return Session.from_dict(data)

    def list_sessions(self) -> list[dict]:
        """
        列出所有会话

        返回：
            会话信息列表 [{"name": "...", "created_at": "...", "message_count": N}, ...]
        """
        sessions = []

        for filename in os.listdir(self.sessions_dir):
            if not filename.endswith(".json"):
                continue

            filepath = os.path.join(self.sessions_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                sessions.append({
                    "name": filename[:-5],  # 去掉 .json
                    "created_at": data.get("created_at", ""),
                    "message_count": len(data.get("messages", [])),
                    "documents": data.get("loaded_documents", [])
                })
            except Exception:
                continue

        # 按创建时间排序（最新的在前）
        sessions.sort(key=lambda x: x["created_at"], reverse=True)
        return sessions

    def delete(self, name: str) -> bool:
        """
        删除会话

        返回：
            是否成功删除
        """
        if not name.endswith(".json"):
            name = f"{name}.json"

        filepath = os.path.join(self.sessions_dir, name)

        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False


# ========== 测试代码 ==========

if __name__ == "__main__":
    """
    运行测试：python -m src.interface.session
    """
    import tempfile

    print("=" * 60)
    print("Session 模块测试")
    print("=" * 60)

    # 使用临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SessionManager(sessions_dir=tmpdir)

        # 测试1：创建会话
        print("\n[测试 1] 创建会话")
        print("-" * 40)
        session = Session()
        session.add_message("user", "苹果2025年收入是多少？")
        session.add_message("assistant", "根据财报，总净销售额为416,161百万美元 [1]")
        session.add_document("data/FY25.pdf")
        print(f"  消息数: {len(session.messages)}")
        print(f"  文档数: {len(session.loaded_documents)}")

        # 测试2：保存会话
        print("\n[测试 2] 保存会话")
        print("-" * 40)
        path = manager.save(session, "test_session")
        print(f"  保存到: {path}")

        # 测试3：列出会话
        print("\n[测试 3] 列出会话")
        print("-" * 40)
        sessions = manager.list_sessions()
        for s in sessions:
            print(f"  {s['name']}: {s['message_count']} 条消息")

        # 测试4：加载会话
        print("\n[测试 4] 加载会话")
        print("-" * 40)
        loaded = manager.load("test_session")
        print(f"  加载成功: {loaded is not None}")
        print(f"  消息数: {len(loaded.messages)}")
        print(f"  第一条消息: {loaded.messages[0]['content'][:30]}...")

        # 测试5：删除会话
        print("\n[测试 5] 删除会话")
        print("-" * 40)
        deleted = manager.delete("test_session")
        print(f"  删除成功: {deleted}")
        print(f"  剩余会话数: {len(manager.list_sessions())}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
