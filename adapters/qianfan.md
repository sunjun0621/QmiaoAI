# 百度千帆平台适配

> 百度千帆大模型平台是钱喵的推荐运行平台。

## 平台特性

- 原生中文支持，指令理解准确
- 支持系统指令（System Prompt）
- 支持知识库挂载
- 支持多轮对话

## 引擎加载

### 方式 A：使用全量合并版（推荐）

1. 打开千帆平台控制台
2. 创建或选择应用
3. 将 `core/SYSTEM-FULL.md` 全部内容粘贴到系统指令区域
4. 保存

### 方式 B：按顺序拼接

将以下 5 个文件按顺序拼接后粘贴到系统指令区域：

1. `core/SYSTEM.md` — 系统指令和架构概述
2. `core/PACK_LOADER.md` — 经验包加载逻辑
3. `core/RULE_SCANNER.md` — 规则扫描器
4. `core/GATE.md` — 两级 Gate 校验
5. `core/REF_SYNTAX.md` — 引用语法

## 经验包加载

### 方式 A：知识库挂载（推荐）

1. 将 `packs/water-soe-finance/` 目录下的文件上传到千帆知识库
2. 按四层分别创建知识库分区：L1-rules、L2-templates、L3-cases、L4-decision-logs
3. 应用关联知识库

### 方式 B：对话中提供

1. 首次对话时，将 L1 规则文件和 L2 模板文件内容粘贴到对话中
2. AI 在会话期间保持加载状态
3. L3 案例和 L4 决策记录按需提供

## 数据输入

### 方式 A：使用 file_bridge.py 自动转换（推荐）

```bash
python tools/file_bridge.py input <文件路径> [--name <重命名>]
```

支持 PDF、DOC、DOCX、XLSX、XLS、PPTX、TXT、MD、CSV 格式，自动转换为 Markdown 写入 `data-buffer/input/`。扫描版 PDF 自动启用 PaddleOCR 补救转换。

转换完成后，将 `data-buffer/input/` 中的 Markdown 文件内容粘贴到对话中即可。

### 方式 B：千帆平台直接上传

1. 千帆平台支持文件上传，可直接上传 CSV 文件
2. 或手动将数据粘贴到对话中

> 详见 `docs/file-bridge-guide.md`。

## 产出归档

QmiaoAI 产出写入 `data-buffer/output/` 后，使用 file_bridge.py 归档到知识库：

```bash
python tools/file_bridge.py output --dry-run   # 预览建议分类
python tools/file_bridge.py output              # 执行归档
```

自动按内容关键词分类到 `01_数据报表`、`02_财务分析`、`03_运用资料`、`04_归档`，支持去重和元数据标注。

## 已知限制

- 系统指令长度限制：使用 `SYSTEM-FULL.md` 合并版确保在限制内
- 知识库文件数量限制：经验包文件较多时需合并上传
- 多轮对话上下文窗口：长报告生成时注意上下文长度

## 验证步骤

1. 加载引擎后，对 AI 说："你是谁？" — 预期回答包含"钱喵"和"AI 财务助手"
2. 提供一条测试数据，说："分析这个月的产销差" — 预期触发 Gate-1 流程
3. 检查 Gate-1 输出是否包含规则加载清单
4. 检查最终产出是否包含 Gate-2 校验结果
