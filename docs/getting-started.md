# 快速上手指南

> 10 分钟内加载钱喵到你的 AI 平台并完成第一次财务分析。

## 前置准备

- 一个支持系统指令（System Prompt）的 AI 平台（千帆、ChatGPT、Claude 等）
- 基本的财务数据（CSV 或文本格式）
- Python 环境（仅使用工具脚本时需要）

## 第一步：加载引擎

### 方式 A：使用全量合并版（推荐）

直接将 `core/SYSTEM-FULL.md` 的全部内容粘贴到 AI 平台的系统指令区域。这个文件已包含所有 5 个引擎模块。

### 方式 B：按顺序拼接

将以下 5 个文件按顺序拼接后粘贴：

1. `core/SYSTEM.md`
2. `core/PACK_LOADER.md`
3. `core/RULE_SCANNER.md`
4. `core/GATE.md`
5. `core/REF_SYNTAX.md`

### 验证加载

对 AI 说："你是谁？"

预期回答包含"钱喵"和"AI 财务助手"。

## 第二步：加载经验包

### 使用内置水务经验包

将 `packs/water-soe-finance/` 目录下的内容提供给 AI：

- **方式 A**：将 L1-L4 文件内容粘贴到对话中
- **方式 B**：上传到平台的知识库/文档库

### 创建自己的经验包

```bash
python tools/init_pack.py my-finance "我的财务经验包"
```

然后编辑 `packs/my-finance/` 下的文件：
1. `README.md` - 填写经验包说明
2. `L1-rules/core/` - 定义通用规则（会计恒等式、脱敏检查等）
3. `L1-rules/context/` - 定义领域特定规则（带 keywords）
4. `L2-templates/` - 放你常用的报告模板
5. `L3-cases/` - 放脱敏后的案例
6. `L4-decision-logs/` - AI 自动写入，无需手动操作

## 第三步：准备数据

### 使用数据模板

从 `data-buffer/templates/` 复制模板到 `data-buffer/input/`：

| 模板 | 用途 |
|------|------|
| `monthly-data.csv` | 月度财务数据 |
| `budget-data.csv` | 预算数据 |
| `reconciliation.csv` | 勾稽数据 |

### 填入脱敏数据

**重要**：数据脱敏由你全权负责。确保删除或替换所有银行账号、身份证号、手机号等敏感信息。

### 直接粘贴

也可以不使用模板，直接在对话中粘贴 CSV 或文本格式的数据。

## 第四步：开始使用

### 场景一：月度财务分析

```
用水务经验包分析这个月的产销差数据
```

AI 将：
1. Gate-1 确认数据格式和脱敏状态
2. 加载 L1 规则（core 全部 + context 命中的文件）
3. 按 L2 月度分析模板处理
4. 参考 L3 历史案例
5. Gate-2 校验产出
6. 输出分析报告 + 提示清单
7. 自动记录 L4 决策日志

### 场景二：预算执行分析

```
分析本月水费收入预算执行情况
```

触发 variance + anomaly 规则，重点检查预算偏差。

### 场景三：轻量检查

```
看看这个季度的运营成本有没有异常
```

轻量模式，跳过 L2 模板编排，直接分析，Gate-2 仍执行。

### 场景四：编制报表

```
按 [L2:balance-sheet] 模板编制资产负债表
```

使用引用语法直接指定模板。

### 场景五：经济效益月报

```
编制本月经济效益月报
```

按财资〔2025〕161号文件格式编制国有企业经济效益月报。

## 理解输出

### Gate-1 输出

```
─── Gate-1 数据准入 ───
[Info] 数据格式：CSV（3列 x 15行），符合月度分析要求
[Info] 脱敏提示：请确认数据已脱敏（本次提示，后续不再重复）
[Info] 本次加载规则：core(全部) + context(anomaly, audit, variance)
[Info] 处理计划：使用 [L2:monthly-analysis] 模板
─── Gate-1 通过（非阻断）───
```

### Gate-2 输出

两个区块：规则扫描结果 + 独立审查报告。所有校验均为非阻断式，不影响交付。

### 规则扫描提示

提示按严重性排序：Alert > Warn > Info。每条提示标注规则来源。

### Instinct 召回

- `[Instinct·Auto]`：confidence >= 0.7，自动应用
- `[Instinct·Hint]`：confidence < 0.7，仅提示

## 工具脚本

### 校验经验包

```bash
python tools/validate_pack.py packs/water-soe-finance/
```

检查目录结构、规则字段完整性、案例脱敏。

### 安全扫描

```bash
python tools/scan_pack.py --all
```

检测 prompt injection 风险，按 Alert/Warn/Info 分级。

### 创建经验包

```bash
python tools/init_pack.py manufacturing "制造业财务经验包"
```

从 _template 创建新的经验包目录。

## 常见问题

**Q：数据安全吗？**

A：数据安全由你全权负责。AI 不拥有、不修改、不存储你的数据。Gate-1 会提示确认脱敏，但脱敏责任在用户。

**Q：Gate 校验失败会怎样？**

A：不会"失败"。所有 Gate 校验均为非阻断式，只输出提示。你可以根据提示修正产出，也可以忽略提示直接使用。

**Q：如何添加自定义规则？**

A：在经验包的 `L1-rules/context/` 下创建 `.yml` 文件，按规则格式编写。core 规则放 `L1-rules/core/`。

**Q：如何添加自定义模板？**

A：在 `L2-templates/` 下创建 `.md` 文件，头部声明引用的 L1 规则，然后定义任务流程和产出格式。

**Q：支持哪些 AI 平台？**

A：任何支持系统指令的 AI 平台。详见 `adapters/` 下的适配器说明。

**Q：L4 决策记录在哪？**

A：AI 在每次 Gate-2 通过后自动写入 `L4-decision-logs/` 目录。你不需要手动创建，但可以随时编辑历史记录。

**Q：Instinct 怎么用？**

A：Instinct 是从历史决策提炼的直觉经验卡片。你可以在 `L4-decision-logs/instincts/` 下手动创建 `.yml` 文件，或在用户纠正 AI 判断时由 AI 自动提取。confidence >= 0.7 的 instinct 会在匹配时自动应用。
