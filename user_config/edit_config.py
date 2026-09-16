#!/usr/bin/env python3
"""Interactive, comment-preserving editor for MAA Online daily.toml."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(os.getenv("MAA_ONLINE_ROOT", Path(__file__).resolve().parents[1]))
DEFAULT_FILE = Path(os.getenv("MAA_ONLINE_CONFIG_FILE", Path(__file__).with_name("daily.toml")))
MAA_DRY_RUN = [
    str(ROOT / "bin/maa-online"),
    "run",
    "daily",
    "--dry-run",
    "--batch",
]
KEY_RE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_]+)(?P<space>\s*=\s*)(?P<value>.*?)(?P<newline>\r?\n)?$")


def toml_literal(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_literal(item) for item in value) + "]"
    if isinstance(value, dict):
        pairs = [f"{toml_literal(str(key))} = {toml_literal(item)}" for key, item in value.items()]
        return "{ " + ", ".join(pairs) + " }"
    raise TypeError(f"不支持的值类型：{type(value).__name__}")


def parse_value(raw: str, current: Any) -> Any:
    text = raw.strip()
    if isinstance(current, bool):
        aliases = {
            "true": True, "yes": True, "y": True, "1": True, "是": True, "开": True,
            "false": False, "no": False, "n": False, "0": False, "否": False, "关": False,
        }
        value = aliases.get(text.lower())
        if value is None:
            raise ValueError("布尔值请输入 true/false、yes/no、是/否或开/关")
        return value

    if isinstance(current, str) and not text.startswith(('"', "'")):
        return text

    if isinstance(current, list) and not text.startswith("["):
        parts = [part.strip() for part in text.split(",") if part.strip()]
        if not parts:
            return []
        sample = current[0] if current else ""
        if isinstance(sample, int):
            return [int(part) for part in parts]
        return parts

    try:
        return tomllib.loads("value = " + text)["value"]
    except (tomllib.TOMLDecodeError, KeyError) as exc:
        raise ValueError(f"无法解析 TOML 值：{exc}") from exc


def same_kind(current: Any, value: Any) -> bool:
    if isinstance(current, bool):
        return isinstance(value, bool)
    if isinstance(current, int) and not isinstance(current, bool):
        return isinstance(value, int) and not isinstance(value, bool)
    if isinstance(current, float):
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, type(current))


class ConfigEditor:
    def __init__(self, path: Path, maa_validate: bool = True):
        self.path = path.resolve()
        self.maa_validate = maa_validate and self.path == DEFAULT_FILE.resolve()
        self.original_text = self.path.read_text(encoding="utf-8")
        self.text = self.original_text

    def data(self) -> dict[str, Any]:
        return tomllib.loads(self.text)

    def sections(self) -> list[tuple[str, int | None, dict[str, Any]]]:
        data = self.data()
        global_values = {key: value for key, value in data.items() if key != "tasks"}
        result: list[tuple[str, int | None, dict[str, Any]]] = [("全局", None, global_values)]
        for index, task in enumerate(data.get("tasks", [])):
            label = f"{task.get('name', task.get('type', '任务'))} [{task.get('type', '?')}]"
            result.append((label, index, task.get("params", {})))
        return result

    def replace(self, task_index: int | None, key: str, value: Any) -> None:
        lines = self.text.splitlines(keepends=True)
        current_task = -1
        in_params = False
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped == "[[tasks]]":
                current_task += 1
                in_params = False
                continue
            if stripped == "[tasks.params]":
                in_params = True
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                in_params = False

            matches_section = current_task == -1 if task_index is None else current_task == task_index and in_params
            if not matches_section:
                continue
            match = KEY_RE.match(line)
            if not match or match.group("key") != key:
                continue
            newline = match.group("newline") or ""
            lines[index] = f"{match.group('indent')}{key}{match.group('space')}{toml_literal(value)}{newline}"
            self.text = "".join(lines)
            self.data()  # 再次解析，确保生成结果仍是合法 TOML。
            return
        raise KeyError(f"找不到配置项：{key}")

    def save(self) -> Path:
        self.data()
        backup_dir = self.path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup = backup_dir / f"{self.path.name}.{stamp}.bak"
        suffix = 1
        while backup.exists():
            backup = backup_dir / f"{self.path.name}.{stamp}.{suffix}.bak"
            suffix += 1
        shutil.copy2(self.path, backup)

        mode = self.path.stat().st_mode & 0o777
        fd, temp_name = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
                handle.write(self.text)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_name, mode)
            os.replace(temp_name, self.path)
        except Exception:
            Path(temp_name).unlink(missing_ok=True)
            raise

        if self.maa_validate:
            result = subprocess.run(MAA_DRY_RUN, text=True, capture_output=True, timeout=120)
            if result.returncode != 0:
                shutil.copy2(backup, self.path)
                detail = (result.stderr or result.stdout).strip()
                raise RuntimeError(f"MAA dry-run 失败，已自动回滚：\n{detail}")
            print(result.stdout.strip())

        self.original_text = self.text
        return backup

    @property
    def changed(self) -> bool:
        return self.text != self.original_text


def edit_section(editor: ConfigEditor, task_index: int | None, label: str) -> None:
    while True:
        section = next(values for section_label, index, values in editor.sections() if section_label == label and index == task_index)
        keys = list(section)
        print(f"\n=== {label} ===")
        for number, key in enumerate(keys, 1):
            print(f"{number:2}. {key} = {toml_literal(section[key])}")
        print(" b. 返回")
        choice = input("选择配置项：").strip().lower()
        if choice in {"b", "back", "返回", ""}:
            return
        try:
            key = keys[int(choice) - 1]
        except (ValueError, IndexError):
            print("无效选择。")
            continue

        current = section[key]
        print(f"当前值：{toml_literal(current)}")
        raw = input("新值（直接回车取消；列表可用逗号分隔）：")
        if not raw.strip():
            continue
        try:
            value = parse_value(raw, current)
            if not same_kind(current, value):
                raise ValueError(f"类型不匹配，需要 {type(current).__name__}")
            editor.replace(task_index, key, value)
            print(f"已暂存：{key} = {toml_literal(value)}")
        except (KeyError, TypeError, ValueError) as exc:
            print(f"修改失败：{exc}")


def interactive(editor: ConfigEditor) -> int:
    while True:
        print("\n=== MAA Online TOML 配置编辑器 ===")
        for number, (label, _, _) in enumerate(editor.sections(), 1):
            print(f"{number:2}. {label}")
        print(" s. 保存并验证" + (" *" if editor.changed else ""))
        print(" q. 退出")
        choice = input("请选择：").strip().lower()
        if choice in {"q", "quit", "退出"}:
            if editor.changed:
                confirm = input("存在未保存修改，确认丢弃？[y/N] ").strip().lower()
                if confirm not in {"y", "yes", "是"}:
                    continue
            return 0
        if choice in {"s", "save", "保存"}:
            if not editor.changed:
                print("没有需要保存的修改。")
                continue
            try:
                backup = editor.save()
                print(f"保存成功；备份：{backup}")
            except Exception as exc:
                print(f"保存失败：{exc}")
            continue
        try:
            label, task_index, _ = editor.sections()[int(choice) - 1]
        except (ValueError, IndexError):
            print("无效选择。")
            continue
        edit_section(editor, task_index, label)


def main() -> int:
    parser = argparse.ArgumentParser(description="交互式编辑 MAA Online TOML 配置")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE, help="要编辑的 TOML 文件")
    parser.add_argument("--no-maa-validate", action="store_true", help="保存时不运行 MAA dry-run")
    args = parser.parse_args()
    if not args.file.is_file():
        parser.error(f"配置文件不存在：{args.file}")
    editor = ConfigEditor(args.file, maa_validate=not args.no_maa_validate)
    try:
        return interactive(editor)
    except (EOFError, KeyboardInterrupt):
        print("\n已取消，未保存的修改不会写入文件。")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
