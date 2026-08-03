# file_bridge.py 使用指南

> QmiaoAI 数据桥接工具 — 连接外部文件与 QmiaoAI 数据层

## 定位

file_bridge.py 是 QmiaoAI 的数据入口和出口工具，不参与引擎处理流程。它解决两个问题：

1. **输入**：把各种格式的财务文件（PDF/Word/Excel 等）转成 Markdown，放进 `data-buffer/input/` 供 QmiaoAI 处理
2. **输出**：把 QmiaoAI 的产出（`data-buffer/output/`）归档到知识库，按内容自动建议分类

## 安装依赖

```bash
pip install markitdown          # 文档转换
pip install paddlepaddle==3.2.2  # OCR 引擎（扫描版 PDF 补救，必须 3.2.2）
pip install paddleocr==3.7.0     # OCR 接口
```

> PaddlePaddle 3.3.x 在 Windows CPU 上有 oneDNN 兼容性 BUG，必须用 3.2.2。

## 命令

### input — 输入桥

```bash
python tools/file_bridge.py input <文件路径> [--name <重命名>]
```

把文件转为 Markdown 放入 `data-buffer/input/`。

**支持的格式**：PDF、DOC、DOCX、XLSX、XLS、PPTX、TXT、MD、CSV

**转换流程**：

```
文件 → [.doc? Word COM 转 .docx] → markitdown API 转 Markdown
                                         ↓
                                   转换后 <500 字节且为 PDF?
                                         ↓ 是
                                   PaddleOCR 二次转换（补救扫描版）
                                         ↓
                                   写入 data-buffer/input/{名称}.md
```

**参数**：

| 参数 | 说明 |
|------|------|
| `<文件路径>` | 源文件路径（必填） |
| `--name <重命名>` | 指定输出文件名（不含扩展名，自动加 .md） |

**重名处理**：内容相同跳过，内容不同加日期后缀。

**安全提示**：每次转换后自动扫描身份证号、银行账号、手机号等敏感信息并警告。数据脱敏由使用者全权负责。

**示例**：

```bash
# 转换 PDF 财报
python tools/file_bridge.py input 6月财务报表.pdf

# 转换 Word 报告并重命名
python tools/file_bridge.py input 分析报告.docx --name 7月水务分析

# 转换 Excel 数据
python tools/file_bridge.py input 预算执行表.xlsx
```

### output — 输出桥

```bash
python tools/file_bridge.py output [--file <文件名>] [--dry-run]
```

把 `data-buffer/output/` 中的产出归档到知识库。

**分类规则**（按优先级匹配，命中即归类）：

| 分类 | 关键词 |
|------|--------|
| 01_数据报表 | 报表、利润表、资产负债表、现金流量表、月报、季报、年报、决算、预算、快报 |
| 02_财务分析 | 分析、报告、经营、预算执行、财务分析、绩效、指标、同比、环比 |
| 03_运用资料 | 办法、管理、制度、规范、规定、会计、票据、核算 |
| 04_归档 | （兜底） |

**参数**：

| 参数 | 说明 |
|------|------|
| `--file <文件名>` | 指定单个文件（支持模糊匹配） |
| `--dry-run` | 仅预览建议，不实际归档 |

**重名处理**：内容相同跳过，内容不同加日期后缀。

**归档元数据**：自动设置 source=QmiaoAI、classification=内部、年度（从文件名提取）。

**示例**：

```bash
# 预览归档建议
python tools/file_bridge.py output --dry-run

# 执行归档（全部）
python tools/file_bridge.py output

# 归档指定文件
python tools/file_bridge.py output --file 7月分析报告.md
```

### status — 状态查看

```bash
python tools/file_bridge.py status
```

显示：
- `data-buffer/input/` 文件列表
- `data-buffer/output/` 文件列表
- 知识库各分类文件数和大小
- 最近 5 条归档记录

## 典型工作流

```
1. 拿到用友导出的财务报表（Excel）
   → python tools/file_bridge.py input 6月报表.xlsx --name 6月财务数据

2. 在 AI 平台加载 QmiaoAI 引擎 + 水务经验包，粘贴 data-buffer/input/6月财务数据.md
   → AI 执行七阶段流水线（Gate-1 → 规则扫描 → AI 处理 → Gate-2）
   → 产出写入 data-buffer/output/

3. 归档产出
   → python tools/file_bridge.py output --dry-run   # 先预览
   → python tools/file_bridge.py output              # 确认后归档
```

## 路径配置

脚本自动从自身位置定位 QmiaoAI 根目录（向上查找 `data-buffer/`）。

知识库路径默认 `D:\0_My_Work\2_财税知识库\`，可通过环境变量覆盖：

```bash
set QMIAO_KB_ROOT=D:\其他路径\知识库
python tools/file_bridge.py status
```

## 注意事项

1. **markitdown 警告**：运行时可能出现 `RuntimeWarning: Couldn't find ffmpeg`，这是音频库提示，不影响文档转换
2. **PaddleOCR 首次加载**：约 10-15 秒，后续复用实例
3. **.doc 转换**：需要 Windows + 已安装 Word（使用 Word COM 组件）
4. **知识库是纯归档仓库**：不做搜索、标签、周报等管理功能，只接收和存储产出
5. **脱敏责任**：工具会检测并警告敏感信息，但脱敏由使用者全权负责
