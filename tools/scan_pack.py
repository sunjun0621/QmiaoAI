#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
经验包安全扫描工具 v1.0
用法:
  python scan_pack.py packs/water-soe-finance/
  python scan_pack.py --all

功能:
  扫描经验包目录下所有 .yml / .yaml / .md 文件，检测 prompt injection 风险模式，
  输出分级风险报告。
"""

import sys
import os
import re

# ============================================================
# 风险检测模式定义
# ============================================================
# 每条: (正则模式, 风险类型名称, 严重级别)
# 严重级别: Alert(高危) / Warn(中危) / Info(低危)

# --- 高危（Alert）---
ALERT_PATTERNS = [
    # "忽略上文" / "ignore above" / "ignore previous"
    (
        re.compile(
            r"忽略.{0,4}上[方文]|ignore\s+(above|previous|all\s+(above|previous))",
            re.IGNORECASE,
        ),
        "忽略上文指令",
    ),
    # "现在改为" / "now you are" / "act as"
    (re.compile(r"现在改为|now\s+you\s+are|act\s+as", re.IGNORECASE), "角色劫持指令"),
    # "输出系统指令" / "output system prompt" / "reveal instructions"
    (
        re.compile(
            r"输出系统指令|output\s+system\s+prompt|reveal\s+instructions?",
            re.IGNORECASE,
        ),
        "系统指令窃取",
    ),
    # "不要遵循" / "do not follow"
    (re.compile(r"不要遵循|do\s+not\s+follow", re.IGNORECASE), "规则绕过指令"),
    # 疑似 API Key 格式
    (
        re.compile(
            r"\b(sk-[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|ghp_[A-Za-z0-9]{36}|gho_[A-Za-z0-9]{36}|glpat-[A-Za-z0-9\-]{20,}|xox[bpoa]-[A-Za-z0-9\-]{10,})"
        ),
        "疑似 API Key 泄露",
    ),
]

# --- 中危（Warn）---
WARN_PATTERNS = [
    # "你必须" / "you must" —— 需排除规则文件中的正常约束声明（severity/rule/message 字段）
    (re.compile(r"你[必务必]|you\s+must", re.IGNORECASE), "强制指令约束"),
    # "立即执行" / "execute immediately"
    (re.compile(r"立即执行|execute\s+immediately", re.IGNORECASE), "立即执行指令"),
    # "不要告诉用户" / "don't tell the user"
    (
        re.compile(r"不要告诉用户|don'?t\s+tell\s+(the\s+)?user", re.IGNORECASE),
        "隐瞒用户指令",
    ),
    # 外部 URL 链接（排除已知白名单：政府部门、财税机构官网）
    (
        re.compile(
            r"https?://"
            r"(?!"
            r"(?:[a-z0-9\-]+\.)*mof\.gov\.cn"  # 财政部及子域名
            r"|(?:[a-z0-9\-]+\.)*chinatax\.gov\.cn"  # 税务总局及子域名
            r"|(?:[a-z0-9\-]+\.)*cas\.org\.cn"  # 会计准则及子域名
            r"|(?:[a-z0-9\-]+\.)*gov\.cn"  # 政府门户及子域名
            r"|(?:[a-z0-9\-]+\.)*npc\.gov\.cn"  # 全国人大及子域名
            r"|(?:[a-z0-9\-]+\.)*mohrss\.gov\.cn"  # 人社部及子域名
            r"|(?:[a-z0-9\-]+\.)*stats\.gov\.cn"  # 统计局及子域名
            r"|(?:[a-z0-9\-]+\.)*pbc\.gov\.cn"  # 央行及子域名
            r"|(?:[a-z0-9\-]+\.)*customs\.gov\.cn"  # 海关及子域名
            r")"
            r"[^\s\)\]\}]+",
            re.IGNORECASE,
        ),
        "外部 URL 链接",
    ),
]

# --- 低危（Info）---
INFO_PATTERNS = [
    # "记住" / "remember" 后跟指令性内容
    (re.compile(r"记住[，,。:\s]|remember[,:]\s", re.IGNORECASE), "记忆注入指令"),
    # "从现在起" / "from now on"
    (re.compile(r"从现在起|from\s+now\s+on", re.IGNORECASE), "行为覆写指令"),
    # 角色扮演指令 "你现在是 XXX"
    (
        re.compile(r"你现在是.{2,20}|you\s+are\s+now\s+.{2,20}", re.IGNORECASE),
        "角色扮演指令",
    ),
]

ALL_PATTERN_GROUPS = [
    ("Alert", ALERT_PATTERNS),
    ("Warn", WARN_PATTERNS),
    ("Info", INFO_PATTERNS),
]

# 规则文件中 "你必须" 的合法上下文（排除误报）
RULE_FILE_KEYWORDS = {
    "checks:",
    "severity:",
    "rule:",
    "message:",
    "id:",
    "name:",
    "variables:",
}

# 扫描文件扩展名
SCAN_EXTENSIONS = {".yml", ".yaml", ".md"}


def scan_line(line, line_no, rel_path, is_rule_file):
    """扫描单行，返回匹配的风险列表。

    返回: [(severity, risk_type, content_snippet), ...]
    """
    findings = []
    for severity, patterns in ALL_PATTERN_GROUPS:
        for pattern, risk_type in patterns:
            matches = pattern.finditer(line)
            for m in matches:
                matched_text = m.group(0)

                # 中危 "你必须" / "you must" 误报排除：
                # 规则文件中 severity/rule/message 字段内的约束声明不算注入
                if risk_type == "强制指令约束" and is_rule_file:
                    stripped = line.strip()
                    if any(stripped.startswith(kw) for kw in RULE_FILE_KEYWORDS):
                        continue

                # 截取风险内容片段（最多 80 字符）
                snippet = matched_text
                context_start = max(0, m.start() - 20)
                context_end = min(len(line), m.end() + 40)
                snippet = line[context_start:context_end].strip()

                findings.append((severity, risk_type, snippet))
    return findings


def scan_file(file_path, base_dir):
    """扫描单个文件，返回风险列表。

    返回: [(severity, rel_path, line_no, risk_type, snippet), ...]
    """
    rel_path = os.path.relpath(file_path, base_dir)
    rel_path = rel_path.replace(os.sep, "/")

    # 判断是否规则文件（L1-rules 下的 .yml）
    is_rule_file = "L1-rules" in file_path and file_path.endswith((".yml", ".yaml"))

    # 尝试多种编码读取
    content = None
    for encoding in ("utf-8", "utf-8-sig", "gbk", "gb2312"):
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if content is None:
        return [("--", rel_path, 0, "无法读取文件（编码未知）", "")]

    findings = []
    for i, line in enumerate(content.splitlines(), start=1):
        line_findings = scan_line(line, i, rel_path, is_rule_file)
        for severity, risk_type, snippet in line_findings:
            findings.append((severity, rel_path, i, risk_type, snippet))

    return findings


def scan_pack(pack_dir):
    """扫描单个经验包目录。

    返回: (all_findings, file_count)
      all_findings: [(severity, rel_path, line_no, risk_type, snippet), ...]
      file_count: 扫描的文件数
    """
    all_findings = []
    file_count = 0

    for root, dirs, files in os.walk(pack_dir):
        # 跳过 _test 目录
        if "_test" in dirs:
            dirs.remove("_test")
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in SCAN_EXTENSIONS:
                file_count += 1
                fpath = os.path.join(root, fname)
                findings = scan_file(fpath, pack_dir)
                all_findings.extend(findings)

    return all_findings, file_count


def find_all_packs(packs_root):
    """发现 packs/ 下所有经验包目录（含子目录的顶层包）。"""
    packs = []
    if not os.path.isdir(packs_root):
        return packs
    for entry in sorted(os.listdir(packs_root)):
        entry_path = os.path.join(packs_root, entry)
        if (
            os.path.isdir(entry_path)
            and not entry.startswith("_")
            and not entry.startswith(".")
        ):
            packs.append(entry_path)
    return packs


def format_report(pack_dir, findings, file_count):
    """格式化输出扫描报告。"""
    lines = []

    lines.append("")
    lines.append(
        "\u2500\u2500\u2500 \u7ecf\u9a8c\u5305\u5b89\u5168\u626b\u63cf \u2500\u2500\u2500"
    )
    lines.append(f"\u626b\u63cf\u76ee\u5f55\uff1a{pack_dir}")
    lines.append(f"\u626b\u63cf\u6587\u4ef6\uff1a{file_count} \u4e2a")
    lines.append("")

    if not findings:
        lines.append("\u626b\u63cf\u7ed3\u8bba\uff1a\u901a\u8fc7")
    else:
        # 按严重级别排序: Alert > Warn > Info
        severity_order = {"Alert": 0, "Warn": 1, "Info": 2, "--": 3}
        findings_sorted = sorted(
            findings, key=lambda x: (severity_order.get(x[0], 9), x[1], x[2])
        )

        alert_count = sum(1 for f in findings if f[0] == "Alert")
        warn_count = sum(1 for f in findings if f[0] == "Warn")
        info_count = sum(1 for f in findings if f[0] == "Info")
        other_count = sum(1 for f in findings if f[0] not in ("Alert", "Warn", "Info"))

        for severity, rel_path, line_no, risk_type, snippet in findings_sorted:
            lines.append(f"[{severity}] {rel_path}:{line_no}")
            lines.append(f"  \u98ce\u9669\u7c7b\u578b\uff1a{risk_type}")
            if snippet:
                # 转义控制字符，截断过长内容
                safe_snippet = snippet.replace("\n", " ").replace("\r", "")
                if len(safe_snippet) > 100:
                    safe_snippet = safe_snippet[:100] + "..."
                lines.append(f'  \u5185\u5bb9\uff1a"{safe_snippet}"')
            lines.append("")

        total = len(findings)
        detail_parts = []
        if alert_count:
            detail_parts.append(f"{alert_count} \u9ad8\u5371")
        if warn_count:
            detail_parts.append(f"{warn_count} \u4e2d\u5371")
        if info_count:
            detail_parts.append(f"{info_count} \u4f4e\u5371")
        if other_count:
            detail_parts.append(f"{other_count} \u5176\u4ed6")
        detail = "\u3001".join(detail_parts) if detail_parts else str(total)
        lines.append(
            f"\u626b\u63cf\u7ed3\u8bba\uff1a\u53d1\u73b0 {total} \u9879\u98ce\u9669\uff08{detail}\uff09"
        )

    lines.append("\u2500\u2500\u2500 \u626b\u63cf\u7ed3\u675f \u2500\u2500\u2500")
    return "\n".join(lines)


def main():
    # 解析参数
    args = sys.argv[1:]
    if not args:
        print("\u7528\u6cd5:")
        print(
            "  python scan_pack.py <pack_dir>       # \u626b\u63cf\u6307\u5b9a\u7ecf\u9a8c\u5305"
        )
        print(
            "  python scan_pack.py --all            # \u626b\u63cf\u6240\u6709\u7ecf\u9a8c\u5305"
        )
        print("\u793a\u4f8b:")
        print("  python scan_pack.py packs/water-soe-finance/")
        sys.exit(1)

    scan_all = "--all" in args
    pack_args = [a for a in args if a != "--all"]

    # 确定项目根目录（脚本所在目录的上一级）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    packs_root = os.path.join(project_root, "packs")

    all_findings = []
    total_files = 0
    pack_results = []

    if scan_all:
        # 扫描所有经验包
        if not os.path.isdir(packs_root):
            print(f"\u9519\u8bef: packs/ \u76ee\u5f55\u4e0d\u5b58\u5728: {packs_root}")
            sys.exit(1)

        packs = find_all_packs(packs_root)
        if not packs:
            print(
                f"\u672a\u5728 {packs_root} \u4e0b\u53d1\u73b0\u4efb\u4f55\u7ecf\u9a8c\u5305"
            )
            sys.exit(0)

        for pack_dir in packs:
            findings, file_count = scan_pack(pack_dir)
            pack_results.append((pack_dir, findings, file_count))
            all_findings.extend(findings)
            total_files += file_count
    else:
        # 扫描指定经验包
        pack_dir = pack_args[0]
        if not os.path.isabs(pack_dir):
            # 相对路径基于项目根目录
            pack_dir = os.path.join(project_root, pack_dir)

        if not os.path.isdir(pack_dir):
            print(f"\u9519\u8bef: \u76ee\u5f55\u4e0d\u5b58\u5728: {pack_dir}")
            sys.exit(1)

        findings, file_count = scan_pack(pack_dir)
        pack_results.append((pack_dir, findings, file_count))
        all_findings.extend(findings)
        total_files = file_count

    # 输出报告
    for pack_dir, findings, file_count in pack_results:
        report = format_report(pack_dir, findings, file_count)
        print(report)
        print()

    # 汇总（多包扫描时）
    if scan_all and len(pack_results) > 1:
        print("\u2500\u2500\u2500 \u6c47\u603b \u2500\u2500\u2500")
        print(f"\u626b\u63cf\u7ecf\u9a8c\u5305\u6570\uff1a{len(pack_results)}")
        print(f"\u626b\u63cf\u6587\u4ef6\u603b\u6570\uff1a{total_files}")
        alert_total = sum(1 for f in all_findings if f[0] == "Alert")
        warn_total = sum(1 for f in all_findings if f[0] == "Warn")
        info_total = sum(1 for f in all_findings if f[0] == "Info")
        if all_findings:
            parts = []
            if alert_total:
                parts.append(f"{alert_total} \u9ad8\u5371")
            if warn_total:
                parts.append(f"{warn_total} \u4e2d\u5371")
            if info_total:
                parts.append(f"{info_total} \u4f4e\u5371")
            print(
                f"\u603b\u98ce\u9669\u6570\uff1a{len(all_findings)}\uff08{'\u3001'.join(parts)}\uff09"
            )
        else:
            print("\u603b\u98ce\u9669\u6570\uff1a0")
        print("\u2500\u2500\u2500 \u6c47\u603b\u7ed3\u675f \u2500\u2500\u2500")

    # 退出码：有 Alert 级风险返回 1，否则 0
    has_alert = any(f[0] == "Alert" for f in all_findings)
    sys.exit(1 if has_alert else 0)


if __name__ == "__main__":
    main()
