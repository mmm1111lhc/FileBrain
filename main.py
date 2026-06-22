#!/usr/bin/env python3
"""FileBrain · 文件大脑

桌面文件智能整理工具：
  - 自动扫描文件内容
  - 智能重命名（内容摘要 + 日期 + 版本号）
  - 支持 PDF（含扫描件 OCR）、Word、Excel、图片
  - 全文检索，快速定位文件
  - 发送留痕，记录文件分享历史

用法：
  python main.py             启动图形界面
  python main.py --scan ~/Desktop  扫描指定目录
"""

import os
import sys
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("FileBrain")


def main():
    parser = argparse.ArgumentParser(
        description="FileBrain · 文件大脑 —— 桌面文件智能整理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python main.py                    启动图形界面
  python main.py --scan ~/Desktop   扫描桌面文件
  python main.py --version          查看版本
        """,
    )
    parser.add_argument("--scan", metavar="目录",
                        help="扫描指定目录下的文件")
    parser.add_argument("--version", action="store_true",
                        help="显示版本信息")
    parser.add_argument("--cli", action="store_true",
                        help="使用命令行模式（无GUI）")

    args = parser.parse_args()

    if args.version:
        print("FileBrain · 文件大脑  v1.0")
        print("桌面文件智能整理工具")
        return

    if args.scan:
        from core.watcher import Watcher
        watch_dir = args.scan
        logger.info(f"扫描目录: {watch_dir}")
        watcher = Watcher(watch_dir)
        watcher.start()
        watcher.stop()
        idx_count = watcher.search_index.count()
        logger.info(f"扫描完成，已索引 {idx_count} 个文件")
        return

    if args.cli:
        # CLI 交互模式（简单版）
        _cli_mode()
    else:
        # 启动 GUI
        _gui_mode()


def _gui_mode():
    """启动图形界面"""
    try:
        from gui.app import main as gui_main
        gui_main()
    except ImportError as e:
        logger.error(f"GUI 启动失败: {e}")
        logger.error("请确认 tkinter 已安装: brew install python-tk")
        sys.exit(1)


def _cli_mode():
    """命令行交互模式"""
    from core.watcher import Watcher
    from core.journal import SendJournal

    print("🧠 FileBrain · 文件大脑  CLI 模式")
    watch_dir = input("请输入要监控的目录 (默认: ~/Desktop): ").strip()
    if not watch_dir:
        watch_dir = os.path.expanduser("~/Desktop")

    watcher = Watcher(watch_dir)
    journal = SendJournal(watch_dir)

    print(f"监控目录: {watch_dir}")
    print("命令: start | stop | search <关键词> | send | status | exit")

    while True:
        try:
            cmd = input("\n> ").strip().lower()
            if cmd == "exit":
                break
            elif cmd == "start":
                watcher.start()
            elif cmd == "stop":
                watcher.stop()
            elif cmd.startswith("search "):
                query = cmd[7:]
                results = watcher.search_index.search(query)
                print(f"找到 {len(results)} 个结果:")
                for r in results:
                    print(f"  📄 {r['new_name']} (相关度: {r['score']})")
                    print(f"     {r.get('context', '')}")
            elif cmd == "send":
                _cli_send_dialog(watcher, journal)
            elif cmd == "status":
                print(f"监控运行中: {watcher.is_running()}")
                print(f"已索引文件: {watcher.search_index.count()}")
            else:
                print("未知命令")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"错误: {e}")

    if watcher.is_running():
        watcher.stop()
    print("再见！")


def _cli_send_dialog(watcher, journal):
    """CLI 发送记录录入"""
    query = input("搜索要记录的文件: ").strip()
    if not query:
        return
    results = watcher.search_index.search(query)
    if not results:
        print("未找到匹配文件")
        return

    print("匹配文件:")
    for i, r in enumerate(results[:5], 1):
        print(f"  {i}. {r['new_name']}")
    try:
        idx = int(input("选择序号: ")) - 1
        if idx < 0 or idx >= len(results):
            return
    except ValueError:
        return

    file_path = results[idx]["path"]
    file_name = results[idx]["new_name"]
    print(f"文件: {file_name}")

    recipient = input("接收人: ").strip()
    if not recipient:
        return
    method = input("发送方式 (微信/邮件/AirDrop/其他): ").strip()
    notes = input("备注 (可选): ").strip()

    record = journal.add_record(file_path, file_name,
                                recipient, method, notes)
    print(f"✅ 记录已保存 (ID: {record['id']})")


if __name__ == "__main__":
    main()
