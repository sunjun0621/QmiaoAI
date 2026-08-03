# -*- coding: utf-8 -*-
"""
file_bridge.py - QmiaoAI 数据桥接工具 v1.0

两个核心命令:
  input  - 输入桥: 任意格式文件 -> markitdown/PaddleOCR 转换 -> data-buffer/input/*.md
  output - 输出桥: data-buffer/output/* -> 分类归档到知识库

辅助命令:
  status - 查看 input/output 目录和知识库状态

依赖:
  - markitdown (系统 Python site-packages)
  - PaddleOCR 3.7.0 + PaddlePaddle 3.2.2 (延迟加载, 扫描版 PDF 补救)
  - Python 3.13+
  - Windows + Word (仅 .doc 转换需要)

用法:
  python tools/file_bridge.py input <文件路径> [--name <重命名>]
  python tools/file_bridge.py output [--file <文件名>] [--dry-run]
  python tools/file_bridge.py status
"""
import os
import sys
import shutil
import re
import json
import hashlib
from datetime import datetime
from pathlib import Path

# ============================================================
# 路径定位: 从脚本位置向上查找 data-buffer/ 确定 QmiaoAI 根目录
# ============================================================
_SCRIPT_DIR = Path(__file__).resolve().parent  # tools/
_QMIAO_ROOT = _SCRIPT_DIR.parent               # QmiaoAI/
_INPUT_DIR = _QMIAO_ROOT / "data-buffer" / "input"
_OUTPUT_DIR = _QMIAO_ROOT / "data-buffer" / "output"

# 知识库根目录 (纯归档仓库, 可通过环境变量覆盖)
_KB_ROOT_ENV = os.environ.get("QMIAO_KB_ROOT")
KB_ROOT = Path(_KB_ROOT_ENV) if _KB_ROOT_ENV else Path("D:/0_My_Work/2_财税知识库")

# 沙箱 Python 通过 sys.path 注入访问系统 Python 的 site-packages
_SYS_PYTHON_SITE = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python313\Lib\site-packages"
if _SYS_PYTHON_SITE not in sys.path:
    sys.path.insert(0, _SYS_PYTHON_SITE)

# PaddlePaddle 3.x oneDNN 兼容性修复
os.environ.setdefault("FLAGS_enable_pir_in_executor", "0")
os.environ.setdefault("FLAGS_use_mkldnn", "0")

# ============================================================
# 配置
# ============================================================

# 需要转换的格式
CONVERTIBLE_EXTS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx"}
# 可直接入库的格式
DIRECT_EXTS = {".md", ".txt", ".csv"}

# 输出桥分类规则 (按优先级匹配)
CATEGORIES = {
    "01_数据报表": {
        "desc": "月度/季度/年度财务报表、国财快报等数据文件",
        "keywords": [
            "报表", "利润表", "资产负债表", "现金流量表", "财务报表",
            "月报", "季报", "年报", "决算", "预算", "快报", "国资", "财政",
            "资负表", "流量表",
        ],
    },
    "02_财务分析": {
        "desc": "财务分析报告、经营分析、预算执行、收入成本分析",
        "keywords": [
            "分析", "报告", "经营", "预算执行", "财务分析",
            "绩效", "指标", "同比", "环比", "差异",
            "收入", "成本", "利润", "费用", "情况说明",
        ],
    },
    "03_运用资料": {
        "desc": "财务部管理办法、规章制度、操作规范",
        "keywords": [
            "办法", "管理", "制度", "规范", "规定",
            "现金", "备用金", "会计", "票据", "核算",
            "费用", "档案", "资产", "预算",
        ],
    },
    "04_归档": {
        "desc": "其他文件归档",
        "keywords": [],
    },
}

# 元数据存储
METADATA_FILE = KB_ROOT / ".metadata.json"

# 归档日志
ARCHIVE_LOG = KB_ROOT / ".archive_log.json"

# 默认元数据
DEFAULT_METADATA = {
    "classification": "内部",
    "importance": "一般",
    "year": None,
    "source": None,
    "tags": [],
    "remark": None,
    "archived_at": None,
}


# ============================================================
# 文档转换引擎 (markitdown API + PaddleOCR 补救)
# ============================================================
_markitdown_converter = None
_ocr_engine = None


def _get_markitdown():
    """延迟初始化 markitdown API 实例"""
    global _markitdown_converter
    if _markitdown_converter is None:
        from markitdown import MarkItDown
        _markitdown_converter = MarkItDown()
    return _markitdown_converter


def _get_ocr():
    """延迟初始化 PaddleOCR 引擎

    PaddleOCR 3.x API:
      - use_angle_cls -> use_textline_orientation
      - use_gpu 参数已移除
      - 新增 use_doc_orientation_classify / use_doc_unwarping (默认开启, 影响速度)
    """
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR
        _ocr_engine = PaddleOCR(
            lang="ch",
            use_textline_orientation=True,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
        )
    return _ocr_engine


def _doc_to_docx(doc_path, docx_path):
    """使用 Word COM 将 .doc 转换为 .docx (仅 Windows + 已安装 Word)

    返回 True/False
    """
    import subprocess
    ps_script = (
        f"$word = New-Object -ComObject Word.Application; "
        f"$word.Visible = $false; "
        f"$doc = $word.Documents.Open('{doc_path}'); "
        f"$doc.SaveAs([ref]'{docx_path}', [ref]16); "
        f"$doc.Close(); "
        f"$word.Quit(); "
        f"[System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null; "
        f"Write-Output 'OK'"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True, text=True, timeout=60
        )
        return result.returncode == 0 and "OK" in result.stdout
    except Exception:
        return False


def _markitdown_convert(filepath):
    """使用 markitdown API 将文档转换为 Markdown

    返回: (md_text, message)
    """
    try:
        converter = _get_markitdown()
        result = converter.convert(str(filepath))
        md_text = result.text_content
        if md_text and len(md_text.strip()) > 0:
            return md_text, "markitdown 转换成功"
        else:
            return None, "markitdown 转换结果为空"
    except Exception as e:
        return None, f"markitdown 转换异常: {e}"


def _ocr_convert(filepath):
    """使用 PaddleOCR 对扫描版 PDF/图片进行 OCR 转换

    返回: (md_text, message)
    """
    try:
        ocr = _get_ocr()
        result = ocr.predict(str(filepath))
        if not result:
            return None, "PaddleOCR 未识别到文本"

        lines = []
        for page_idx, page_result in enumerate(result):
            if page_result is None:
                continue
            lines.append(f"## 第 {page_idx + 1} 页\n")

            if hasattr(page_result, "rec_texts"):
                texts = page_result.rec_texts or []
                for text in texts:
                    if text:
                        lines.append(text)
            elif isinstance(page_result, dict):
                texts = page_result.get("rec_texts", [])
                for text in texts:
                    if text:
                        lines.append(text)
            elif isinstance(page_result, list):
                for line_info in page_result:
                    if line_info and len(line_info) >= 2:
                        text = line_info[1][0] if line_info[1] else ""
                        if text:
                            lines.append(text)
            lines.append("")

        md_text = "\n".join(lines)
        if len(md_text.strip()) > 0:
            return md_text, f"PaddleOCR 转换完成"
        else:
            return None, "PaddleOCR 转换结果为空"
    except Exception as e:
        return None, f"PaddleOCR 转换异常: {e}"


def convert_file(filepath):
    """转换文件为 Markdown 文本

    返回: (md_text, messages_list)
    - md_text: 转换后的 Markdown 文本, 失败时为 None
    - messages_list: 处理过程中的状态消息列表
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return None, [f"文件不存在: {filepath}"]

    ext = filepath.suffix.lower()
    messages = []

    if ext in CONVERTIBLE_EXTS:
        # .doc 旧格式先转 .docx
        if ext == ".doc":
            docx_path = filepath.parent / (filepath.stem + ".docx")
            if _doc_to_docx(filepath, docx_path):
                filepath = docx_path
                ext = ".docx"
                messages.append(f"已将 .doc 转换为 .docx")
            else:
                messages.append(f".doc -> .docx 转换失败, 尝试直接用 markitdown")

        # 阶段一: markitdown
        md_text, conv_msg = _markitdown_convert(filepath)
        if md_text and len(md_text.strip()) > 0:
            messages.append(conv_msg)

            # 检测转换质量
            if len(md_text.strip()) < 500 and ext == ".pdf":
                messages.append(f"转换后仅 {len(md_text.strip())} 字节, 疑似扫描版 PDF, 启动 PaddleOCR 补救...")
                ocr_text, ocr_msg = _ocr_convert(filepath)
                if ocr_text and len(ocr_text.strip()) > 0:
                    messages.append(ocr_msg)
                    return ocr_text, messages
                else:
                    messages.append(f"PaddleOCR 补救失败: {ocr_msg}")
                    # 返回 markitdown 的结果 (虽然质量差)
                    return md_text, messages
            return md_text, messages
        else:
            # markitdown 失败, 尝试 PaddleOCR
            messages.append(f"{conv_msg}, 尝试 PaddleOCR...")
            ocr_text, ocr_msg = _ocr_convert(filepath)
            if ocr_text and len(ocr_text.strip()) > 0:
                messages.append(ocr_msg)
                return ocr_text, messages
            else:
                messages.append(f"PaddleOCR 也失败: {ocr_msg}")
                return None, messages

    elif ext in DIRECT_EXTS:
        # 直接读取
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                md_text = f.read()
            messages.append(f"直接读取 (无需转换)")
            return md_text, messages
        except Exception as e:
            return None, [f"读取失败: {e}"]
    else:
        return None, [f"不支持的格式: {ext}"]


# ============================================================
# 辅助函数
# ============================================================

def _file_hash(filepath):
    """计算文件 SHA256"""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _text_hash(text):
    """计算文本 SHA256"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _auto_extract_year(filename):
    """从文件名提取年度"""
    matches = re.findall(r"(20[12]\d)", filename)
    if matches:
        return matches[-1]
    return None


def _check_sensitive_content(text):
    """扫描疑似敏感信息"""
    patterns = {
        "身份证号": re.compile(r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b"),
        "银行账号": re.compile(r"\b[1-9]\d{15,18}\b"),
        "手机号": re.compile(r"\b1[3-9]\d{9}\b"),
    }
    hits = []
    for name, pattern in patterns.items():
        matches = pattern.findall(text)
        if matches:
            hits.append(f"{name} x{len(matches)}")
    return hits


def _format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / 1024 / 1024:.1f} MB"


def _get_cli_arg(argv, flag, default=None):
    """从命令行参数提取 --flag 后的值"""
    if flag in argv:
        idx = argv.index(flag)
        if idx + 1 < len(argv):
            return argv[idx + 1]
    return default


# ============================================================
# 元数据管理 (精简版, 仅归档用)
# ============================================================

def _load_metadata():
    """加载全部元数据"""
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_metadata(meta):
    """保存全部元数据"""
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        f.write(json.dumps(meta, ensure_ascii=False, indent=2))


def _get_rel_path(filepath):
    """获取文件相对于知识库根目录的相对路径"""
    try:
        return str(Path(filepath).relative_to(KB_ROOT)).replace("\\", "/")
    except ValueError:
        return str(filepath).replace("\\", "/")


def _set_metadata(filepath, updates):
    """更新文件元数据 (合并写入)"""
    meta = _load_metadata()
    rel = _get_rel_path(filepath)
    if rel not in meta:
        meta[rel] = {}
    for k, v in updates.items():
        if v is None or v == "":
            meta[rel].pop(k, None)
        else:
            meta[rel][k] = v
    if not meta[rel]:
        del meta[rel]
    _save_metadata(meta)


def _remove_metadata(filepath):
    """删除文件元数据"""
    meta = _load_metadata()
    rel = _get_rel_path(filepath)
    if rel in meta:
        del meta[rel]
        _save_metadata(meta)


# ============================================================
# 归档日志
# ============================================================

def _load_archive_log():
    """加载归档日志"""
    if ARCHIVE_LOG.exists():
        try:
            with open(ARCHIVE_LOG, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_archive_log(log):
    """保存归档日志"""
    ARCHIVE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(ARCHIVE_LOG, "w", encoding="utf-8") as f:
        f.write(json.dumps(log, ensure_ascii=False, indent=2))


def _log_archive(entry):
    """记录归档操作"""
    log = _load_archive_log()
    log.append(entry)
    _save_archive_log(log)


# ============================================================
# 知识库索引
# ============================================================

def _generate_index():
    """生成知识库索引文件"""
    index_path = KB_ROOT / "知识库索引.md"
    lines = []
    lines.append("# 财务知识库索引\n")
    lines.append(f"**最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"**知识库路径**: `{KB_ROOT}`\n")
    lines.append("---\n")

    total_files = 0
    for dirname in sorted(CATEGORIES.keys()):
        dirpath = KB_ROOT / dirname
        if not dirpath.exists():
            continue
        files = sorted([f for f in dirpath.iterdir()
                        if f.is_file() and not f.name.startswith(".")
                        and f.name not in ("知识库索引.md",)])
        if not files:
            continue
        desc = CATEGORIES[dirname]["desc"]
        lines.append(f"\n## {dirname} - {desc}\n")
        lines.append(f"({len(files)} 个文件)\n")
        for f in files:
            size = f.stat().st_size
            size_str = _format_size(size)
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")
            lines.append(f"- `{f.name}` ({size_str}, {mtime})\n")
            total_files += 1
    lines.append(f"\n---\n\n")
    lines.append(f"**总计**: {total_files} 个文件\n")
    with open(index_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


# ============================================================
# 输入桥: 文件 -> data-buffer/input/*.md
# ============================================================

def input_bridge(filepath, rename=None):
    """输入桥: 转换文件为 Markdown 并放入 data-buffer/input/

    参数:
        filepath - 源文件路径
        rename   - 可选, 指定输出文件名 (不含扩展名, 自动加 .md)

    返回: dict {status, messages, input_path, ...}
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return {"status": "error", "message": f"文件不存在: {filepath}"}

    # 确保输入目录存在
    _INPUT_DIR.mkdir(parents=True, exist_ok=True)

    ext = filepath.suffix.lower()
    result = {
        "original_file": str(filepath),
        "original_name": filepath.name,
        "original_ext": ext,
        "input_path": None,
        "converted": False,
        "status": "ok",
        "messages": [],
    }

    # 转换文件
    md_text, conv_messages = convert_file(filepath)
    result["messages"].extend(conv_messages)

    if md_text is None:
        result["status"] = "error"
        result["messages"].append("转换失败, 无法生成输入文件")
        return result

    result["converted"] = ext in CONVERTIBLE_EXTS

    # 确定输出文件名
    if rename:
        stem = rename
    else:
        stem = filepath.stem
    output_name = f"{stem}.md"
    output_path = _INPUT_DIR / output_name

    # 重名检测
    if output_path.exists():
        existing_hash = _text_hash(output_path.read_text(encoding="utf-8"))
        new_hash = _text_hash(md_text)
        if existing_hash == new_hash:
            result["status"] = "duplicate"
            result["messages"].append(f"内容相同, 跳过 (已存在: {output_name})")
            result["input_path"] = str(output_path)
            return result
        else:
            timestamp = datetime.now().strftime("%Y%m%d")
            output_name = f"{stem}_{timestamp}.md"
            output_path = _INPUT_DIR / output_name
            result["messages"].append(f"同名但内容不同, 重命名为: {output_name}")

    # 写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    result["input_path"] = str(output_path)
    result["input_name"] = output_name
    result["size"] = output_path.stat().st_size
    result["messages"].append(f"已写入: data-buffer/input/{output_name}")

    # 质量警告
    file_size = output_path.stat().st_size
    if file_size < 500:
        result["messages"].append(
            f"!! 转换后仅 {file_size} 字节, 可能内容极少或转换不完整, 建议检查"
        )

    # 脱敏检查
    sensitive_hits = _check_sensitive_content(md_text)
    if sensitive_hits:
        result["messages"].append(
            f"!! 检测到疑似敏感信息: {sensitive_hits}. 请确认数据已脱敏后再用于 AI 场景"
        )

    # 脱敏提示 (无论是否检测到)
    result["messages"].append("提示: 请确认数据已脱敏, 数据安全由使用者全权负责")

    return result


# ============================================================
# 输出桥: data-buffer/output/* -> 分类归档到知识库
# ============================================================

def _categorize_output(filename, content_preview):
    """根据文件名和内容预览判断归档分类

    返回: (分类名, 命中关键词列表)
    """
    text = filename + " " + (content_preview or "")

    # 按优先级匹配 (01 > 02 > 03, 04 是兜底)
    for cat_name in ["01_数据报表", "02_财务分析", "03_运用资料"]:
        info = CATEGORIES[cat_name]
        hit_keywords = [kw for kw in info["keywords"] if kw in text]
        if hit_keywords:
            return cat_name, hit_keywords

    return "04_归档", []


def output_bridge(filename=None, dry_run=False):
    """输出桥: 将 data-buffer/output/ 中的产出归档到知识库

    参数:
        filename - 可选, 指定单个文件名; None 则处理全部
        dry_run  - True 仅预览, False 执行归档

    返回: dict {status, results, summary}
    """
    if not _OUTPUT_DIR.exists():
        return {"status": "error", "message": f"输出目录不存在: {_OUTPUT_DIR}"}

    # 收集待归档文件
    if filename:
        # 支持文件名和路径
        target = _OUTPUT_DIR / filename if not Path(filename).is_absolute() else Path(filename)
        if not target.exists():
            # 模糊匹配
            matches = list(_OUTPUT_DIR.glob(f"*{filename}*"))
            if len(matches) == 1:
                target = matches[0]
            else:
                return {"status": "error", "message": f"未找到文件: {filename}"}
        files = [target]
    else:
        files = sorted([f for f in _OUTPUT_DIR.iterdir()
                        if f.is_file() and not f.name.startswith(".")
                        and f.suffix.lower() in (".md", ".txt", ".csv")])

    if not files:
        return {"status": "ok", "message": "输出目录为空, 无待归档文件", "results": []}

    # 确保知识库目录存在
    KB_ROOT.mkdir(parents=True, exist_ok=True)
    for cat in CATEGORIES:
        (KB_ROOT / cat).mkdir(parents=True, exist_ok=True)

    results = []

    for f in files:
        # 读取内容前 50 行辅助分类
        content_preview = None
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                content_preview = "".join(fh.readline() for _ in range(50))
        except Exception:
            pass

        category, hit_keywords = _categorize_output(f.name, content_preview)
        auto_year = _auto_extract_year(f.name)

        result = {
            "file": f.name,
            "path": str(f),
            "size": f.stat().st_size,
            "suggested_category": category,
            "hit_keywords": hit_keywords,
            "year": auto_year,
            "action": "preview" if dry_run else "pending",
        }

        if not dry_run:
            # 执行归档
            target_dir = KB_ROOT / category
            target_path = target_dir / f.name

            # 重名检测
            if target_path.exists():
                if _file_hash(f) == _file_hash(target_path):
                    result["action"] = "skip_duplicate"
                    result["message"] = "内容相同, 跳过"
                    results.append(result)
                    continue
                stem = f.stem
                suffix = f.suffix
                timestamp = datetime.now().strftime("%Y%m%d")
                target_path = target_dir / f"{stem}_{timestamp}{suffix}"
                result["renamed"] = target_path.name

            # 复制文件
            shutil.copy2(f, target_path)
            result["action"] = "archived"
            result["archive_path"] = str(target_path)
            result["archive_category"] = category

            # 写入元数据
            meta_updates = {
                "source": "QmiaoAI",
                "classification": "内部",
                "archived_at": datetime.now().isoformat(),
            }
            if auto_year:
                meta_updates["year"] = auto_year
            _set_metadata(target_path, meta_updates)

            # 记录日志
            _log_archive({
                "name": target_path.name,
                "category": category,
                "original_name": f.name,
                "source": "QmiaoAI",
                "archived_at": datetime.now().isoformat(),
                "size": target_path.stat().st_size,
                "year": auto_year,
            })

            result["message"] = f"已归档: {category}/{target_path.name}"

        results.append(result)

    # 更新索引 (非 dry_run 时)
    if not dry_run:
        _generate_index()

    summary = {
        "total": len(results),
        "archived": sum(1 for r in results if r.get("action") == "archived"),
        "skipped": sum(1 for r in results if r.get("action") == "skip_duplicate"),
        "preview": sum(1 for r in results if r.get("action") == "preview"),
    }

    return {"status": "ok", "results": results, "summary": summary}


# ============================================================
# 状态查看
# ============================================================

def show_status():
    """显示 input/output 目录和知识库状态"""
    print("=" * 60)
    print("  QmiaoAI 数据桥接状态")
    print("=" * 60)

    # QmiaoAI 路径
    print(f"\n  QmiaoAI 根目录: {_QMIAO_ROOT}")
    print(f"  知识库根目录:   {KB_ROOT}")

    # input 目录
    print(f"\n  {'─' * 50}")
    print(f"  [输入桥] data-buffer/input/")
    print(f"  {'─' * 50}")
    if _INPUT_DIR.exists():
        input_files = sorted([f for f in _INPUT_DIR.iterdir()
                              if f.is_file() and not f.name.startswith(".")])
        if input_files:
            print(f"  文件数: {len(input_files)}")
            for f in input_files:
                size = _format_size(f.stat().st_size)
                mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"    {f.name:<40s} {size:>10s}  {mtime}")
        else:
            print("  (空)")
    else:
        print("  (目录不存在)")

    # output 目录
    print(f"\n  {'─' * 50}")
    print(f"  [输出桥] data-buffer/output/")
    print(f"  {'─' * 50}")
    if _OUTPUT_DIR.exists():
        output_files = sorted([f for f in _OUTPUT_DIR.iterdir()
                               if f.is_file() and not f.name.startswith(".")])
        if output_files:
            print(f"  文件数: {len(output_files)}")
            for f in output_files:
                size = _format_size(f.stat().st_size)
                mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"    {f.name:<40s} {size:>10s}  {mtime}")
        else:
            print("  (空)")
    else:
        print("  (目录不存在)")

    # 知识库
    print(f"\n  {'─' * 50}")
    print(f"  [归档仓库] {KB_ROOT}")
    print(f"  {'─' * 50}")
    if KB_ROOT.exists():
        total_files = 0
        for cat in sorted(CATEGORIES.keys()):
            cat_dir = KB_ROOT / cat
            if cat_dir.exists():
                files = [f for f in cat_dir.iterdir()
                         if f.is_file() and not f.name.startswith(".")
                         and f.name != "知识库索引.md"]
                count = len(files)
                total_size = sum(f.stat().st_size for f in files)
                print(f"    {cat:<16s} {count:>3d} 个文件  {_format_size(total_size):>10s}")
                total_files += count
            else:
                print(f"    {cat:<16s}   (未创建)")
        print(f"    {'─' * 44}")
        print(f"    {'合计':<16s} {total_files:>3d} 个文件")

        # 最近归档记录
        log = _load_archive_log()
        if log:
            recent = log[-5:]  # 最近 5 条
            print(f"\n  最近归档记录:")
            for entry in reversed(recent):
                ts = entry.get("archived_at", "")[:16].replace("T", " ")
                name = entry.get("name", "?")
                cat = entry.get("category", "?")
                print(f"    {ts}  {cat}/{name}")
    else:
        print("  (知识库未创建)")

    print(f"\n  {'=' * 50}")


# ============================================================
# 使用说明
# ============================================================

def show_usage():
    """显示使用说明"""
    print("""
============================================================
  QmiaoAI 数据桥接工具 (file_bridge.py) v1.0
============================================================

  用法:
    python tools/file_bridge.py input <文件路径> [--name <重命名>]
        输入桥: 转换文件为 Markdown, 放入 data-buffer/input/
        支持: PDF/DOC/DOCX/XLSX/XLS/PPTX/TXT/MD/CSV
        转换: markitdown API + PaddleOCR 补救 (扫描版 PDF)
        重名检测: 内容相同跳过, 内容不同加日期后缀
        示例: python tools/file_bridge.py input 财报.pdf
              python tools/file_bridge.py input 报告.docx --name 7月财务分析

    python tools/file_bridge.py output [--file <文件名>] [--dry-run]
        输出桥: 将 data-buffer/output/ 产出归档到知识库
        分类: 根据文件名和内容关键词自动建议分类
          01_数据报表 - 财务报表/月报/季报/年报等
          02_财务分析 - 分析报告/经营分析/预算执行等
          03_运用资料 - 管理办法/规章制度/操作规范等
          04_归档     - 其他文件
        --dry-run: 仅预览建议, 不实际归档
        --file: 指定单个文件名 (支持模糊匹配)
        示例: python tools/file_bridge.py output --dry-run
              python tools/file_bridge.py output
              python tools/file_bridge.py output --file 7月分析报告.md

    python tools/file_bridge.py status
        状态: 查看 input/output 目录文件和知识库归档概况

  路径:
    QmiaoAI: %s
    知识库:  %s
============================================================
""" % (_QMIAO_ROOT, KB_ROOT))


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_usage()
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "input":
        if len(sys.argv) < 3:
            print("  用法: python tools/file_bridge.py input <文件路径> [--name <重命名>]")
            sys.exit(1)
        filepath = sys.argv[2]
        rename = _get_cli_arg(sys.argv, "--name")
        result = input_bridge(filepath, rename)

        if result["status"] == "ok":
            print(f"\n[OK] 输入桥处理完成")
            for msg in result["messages"]:
                print(f"  {msg}")
            print(f"\n  输入文件: {result.get('input_path', '?')}")
        elif result["status"] == "duplicate":
            print(f"\n[SKIP] 文件已存在, 跳过")
            for msg in result["messages"]:
                print(f"  {msg}")
        else:
            print(f"\n[ERROR] {result.get('message', '处理失败')}")
            for msg in result.get("messages", []):
                print(f"  {msg}")

    elif cmd == "output":
        filename = _get_cli_arg(sys.argv, "--file")
        dry_run = "--dry-run" in sys.argv
        result = output_bridge(filename, dry_run)

        if result["status"] == "error":
            print(f"\n[ERROR] {result.get('message', '处理失败')}")
            sys.exit(1)

        if dry_run:
            print(f"\n[预览] 归档建议 (dry-run, 未实际执行)")
            print(f"  待归档文件: {result['summary']['total']} 个\n")
        else:
            s = result["summary"]
            print(f"\n[OK] 归档完成: {s['archived']} 个归档, {s['skipped']} 个跳过, 共 {s['total']} 个\n")

        for r in result["results"]:
            cat = r["suggested_category"]
            keywords = r.get("hit_keywords", [])
            kw_str = f" (命中: {', '.join(keywords[:3])})" if keywords else ""
            size = _format_size(r.get("size", 0))

            if r.get("action") == "archived":
                renamed = f" -> {r.get('renamed')}" if r.get("renamed") else ""
                print(f"  [归档] {r['file']:<40s} {size:>8s}  -> {cat}{kw_str}{renamed}")
            elif r.get("action") == "skip_duplicate":
                print(f"  [跳过] {r['file']:<40s} {size:>8s}  (内容相同)")
            else:
                print(f"  [建议] {r['file']:<40s} {size:>8s}  -> {cat}{kw_str}")

        if not dry_run and result["results"]:
            print(f"\n  知识库: {KB_ROOT}")

    elif cmd == "status":
        show_status()

    else:
        print(f"  未知命令: {cmd}")
        show_usage()
