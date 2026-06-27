"""发送留痕 —— 记录文件的发送历史：发给谁、什么时间、通过什么方式"""

import json
import time
import hashlib
import logging
from pathlib import Path

from config import STATE_DIR_NAME

logger = logging.getLogger(__name__)

JOURNAL_FILE = "send_journal.json"


class SendJournal:
    """文件发送留痕记录"""

    METHODS = ["微信 WeChat", "邮件 Email", "AirDrop", "钉钉 DingTalk",
               "企业微信 WeCom", "飞书 Feishu", "USB 拷贝", "其他"]

    def __init__(self, watch_dir: str):
        self.watch_dir = Path(watch_dir)
        self.state_dir = self.watch_dir / STATE_DIR_NAME
        self.journal_file = self.state_dir / JOURNAL_FILE
        self._records: list[dict] = []
        self._load()

    def _ensure_dir(self):
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _load(self):
        if self.journal_file.exists():
            try:
                with open(self.journal_file, "r", encoding="utf-8") as f:
                    self._records = json.load(f)
            except Exception as e:
                logger.warning(f"读取发送记录失败: {e}")
                self._records = []
        else:
            self._records = []

    def _save(self):
        self._ensure_dir()
        try:
            with open(self.journal_file, "w", encoding="utf-8") as f:
                json.dump(self._records, f,
                          ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存发送记录失败: {e}")

    def add_record(self, file_path: str, file_name: str,
                   recipient: str, method: str,
                   notes: str = "") -> dict:
        """添加一条发送记录（含哈希校验）"""
        raw = f"{file_path}|{file_name}|{recipient}|{method}|{notes}|{time.time()}"
        record_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
        record = {
            "id": int(time.time() * 1000),
            "file_path": str(Path(file_path).absolute()),
            "file_name": file_name,
            "recipient": recipient.strip(),
            "method": method,
            "notes": notes.strip(),
            "sent_at": time.time(),
            "sent_at_str": time.strftime("%Y-%m-%d %H:%M"),
            "_hash": record_hash,
        }
        self._records.insert(0, record)
        self._save()
        return record

    def verify_record(self, record: dict) -> bool:
        """验证一条记录的哈希是否匹配（检测是否被篡改）"""
        stored_hash = record.get("_hash", "")
        if not stored_hash:
            return False
        raw = f"{record['file_path']}|{record['file_name']}|{record['recipient']}|{record['method']}|{record['notes']}|{record['sent_at']}"
        calc_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return stored_hash == calc_hash

    def verify_all(self) -> dict:
        """验证所有记录，返回 {total, ok, tampered}"""
        total = len(self._records)
        ok = sum(1 for r in self._records if self.verify_record(r))
        return {"total": total, "ok": ok, "tampered": total - ok}

    def delete_record(self, record_id: int) -> bool:
        """删除一条发送记录"""
        count = len(self._records)
        self._records = [r for r in self._records
                         if r.get("id") != record_id]
        if len(self._records) < count:
            self._save()
            return True
        return False

    def get_records_for_file(self, file_path: str) -> list[dict]:
        """获取某个文件的所有发送记录"""
        abs_path = str(Path(file_path).absolute())
        return [r for r in self._records
                if r.get("file_path") == abs_path]

    def search(self, query: str) -> list[dict]:
        """搜索发送记录（按接收人、文件名、备注）"""
        if not query.strip():
            return []
        q = query.lower()
        results = []
        for r in self._records:
            if (q in r.get("recipient", "").lower()
                or q in r.get("file_name", "").lower()
                or q in r.get("notes", "").lower()
                or q in r.get("method", "").lower()):
                results.append(r)
        return results

    def get_recent(self, limit: int = 50) -> list[dict]:
        """获取最近的发送记录"""
        return self._records[:limit]

    def get_all_files_sent(self) -> set:
        """获取所有有发送记录的文件路径"""
        return {r.get("file_path") for r in self._records}

    # ── 联系人管理 ──
    CONTACTS_FILE = "contacts.json"

    @property
    def contacts_file(self):
        return self.state_dir / self.CONTACTS_FILE

    def get_contacts(self) -> list[dict]:
        """获取已保存的联系人列表"""
        f = self.contacts_file
        if f.exists():
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    return json.load(fp)
            except:
                return []
        return []

    def add_contact(self, name: str, department: str = "",
                    method: str = "微信 WeChat") -> dict:
        """添加联系人"""
        contacts = self.get_contacts()
        # 去重（同名替换）
        contacts = [c for c in contacts if c.get("name") != name]
        contact = {"name": name, "department": department,
                   "method": method, "created_at": time.time()}
        contacts.append(contact)
        self._ensure_dir()
        with open(self.contacts_file, "w", encoding="utf-8") as fp:
            json.dump(contacts, fp, ensure_ascii=False, indent=2)
        return contact

    def delete_contact(self, name: str) -> bool:
        """删除联系人"""
        contacts = self.get_contacts()
        before = len(contacts)
        contacts = [c for c in contacts if c.get("name") != name]
        if len(contacts) < before:
            self._ensure_dir()
            with open(self.contacts_file, "w", encoding="utf-8") as fp:
                json.dump(contacts, fp, ensure_ascii=False, indent=2)
            return True
        return False
