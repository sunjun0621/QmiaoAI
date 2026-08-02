# 经验包开发指南

> 本文档介绍如何从零开发一个自定义经验包。

## 概念

经验包是配置层的核心单元，承载某个行业/领域的全部财务知识。一个经验包包含四层：

| 层 | 目录 | 格式 | 内容 |
|----|------|------|------|
| L1 规则 | `L1-rules/` | YAML | 强制约束（公式、阈值、法规） |
| L2 模板 | `L2-templates/` | Markdown | 产出形式（报告骨架、任务流程） |
| L3 案例 | `L3-cases/` | Markdown | 参考经验（历史处理方法） |
| L4 决策 | `L4-decision-logs/` | Markdown + YAML | 决策留痕 + 直觉经验卡片 |

## 创建经验包

### 使用工具创建

```bash
python tools/init_pack.py my-pack "我的经验包"
```

这会从 `_template` 复制完整的四层目录结构到 `packs/my-pack/`。

### 手动创建

```bash
mkdir -p packs/my-pack/L1-rules/core
mkdir -p packs/my-pack/L1-rules/context
mkdir -p packs/my-pack/L2-templates
mkdir -p packs/my-pack/L3-cases
mkdir -p packs/my-pack/L4-decision-logs/instincts
touch packs/my-pack/L4-decision-logs/.gitkeep
```

## L1 规则开发

### 目录结构

```
L1-rules/
├── core/              # 核心规则（始终加载，<=10 条）
│   ├── accounting.yml  # 会计通用规则
│   └── checklist.yml   # 通用自检清单
└── context/           # 上下文规则（关键词触发）
    ├── anomaly.yml     # 异常阈值
    ├── audit.yml       # 审计规则
    └── variance.yml    # 预算执行
```

### core 规则

core 规则始终加载，放置领域无关的通用规则。数量控制在 10 条以内。

```yaml
# L1 核心规则 - 会计核算通用规则
# 始终加载，不受关键词触发影响
# 引用语法: [L1:core:accounting] 指向本文件

checks:
  - id: acc-revenue-cost-profit
    name: 收入-成本-费用=利润
    rule: "收入 - 成本 - 费用 == 利润"
    severity: warn
    message: "核心勾稽关系不平衡，差额 {diff}，请核查"
    variables:
      diff: "计算差额"
```

### context 规则

context 规则按关键词触发加载，放置领域特定规则。

```yaml
# L1 上下文规则 - 异常阈值
# 关键词触发加载
# 引用语法: [L1:context:anomaly] 指向本文件
keywords: [偏差, 异常, 波动, 产销差, 水费]

checks:
  - id: anm-nrw-variance
    name: 产销差率超阈值
    rule: "产销差率 > 0.15"
    severity: warn
    message: "产销差率 {nrw}，超 15% 阈值"
    variables:
      nrw: "产销差率"
```

### 规则字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 唯一标识，建议 `前缀-简述` 格式 |
| `name` | 是 | 规则名称 |
| `rule` | 是 | 规则表达式 |
| `severity` | 是 | `alert` / `warn` / `info` |
| `message` | 是 | 提示消息，支持 `{变量}` 占位 |
| `variables` | 否 | 变量说明 |

### 规则类型

| 类型 | 表达式示例 | 适用场景 |
|------|-----------|----------|
| 数值比较 | `"abs(实际-预算)/预算 > 0.10"` | 阈值检测 |
| 文本匹配 | `"output.contains('银行账号')"` | 敏感信息检测 |
| 勾稽校验 | `"收入 - 成本 - 费用 == 利润"` | 报表平衡 |
| 模板引用 | `"conforms_to([L2:monthly-report])"` | 模板骨架校验 |
| 自定义 | `"由用户定义"` | 扩展逻辑 |

### severity 分级

| 级别 | 定义 | 使用场景 |
|------|------|----------|
| `alert` | 必须修正 | 勾稽不平、敏感信息泄露、规则违反 |
| `warn` | 建议核查 | 超阈值、偏离规范、要素缺失 |
| `info` | 轻微提示 | 格式标注、引用缺失、补充建议 |

### id 命名前缀

| 前缀 | 来源 | 示例 |
|------|------|------|
| `acc-` | core/accounting.yml | `acc-revenue-cost-profit` |
| `cls-` | core/checklist.yml | `cls-desensitize` |
| `anm-` | context/anomaly.yml | `anm-nrw-variance` |
| `aud-` | context/audit.yml | `aud-wsoe-reconciliation` |
| `var-` | context/variance.yml | `var-water-revenue-budget` |

## L2 模板开发

### 文件格式

```markdown
---
rules: [L1:core:accounting], [L1:core:checklist], [L1:context:anomaly]
---

# 任务模板：模板名称

## 任务说明
描述这个模板做什么。

## 输入要求
- 数据来源
- 必要字段
- 可选字段

## 执行步骤
1. Gate-1 确认...
2. 计算指标...
3. 按模板组织内容...
4. Gate-2 校验...

## 产出格式
---

# {公司名称}报告标题

> 数据来源：{来源} | 分析期间：{期间}

## 一、章节一

{内容}

## 二、章节二

{内容}

---

> 本报告由钱喵 AI 财务助手辅助生成，数据脱敏及准确性由使用者负责。
```

### 关键要素

1. **头部 rules 声明**：列出本模板产出必须满足的 L1 规则
2. **任务说明**：描述模板用途
3. **输入要求**：明确需要什么数据
4. **执行步骤**：Gate-1 → 处理 → Gate-2 的完整流程
5. **产出格式**：用 `{占位符}` 标记需要填充的位置，用 `##` 定义章节（Gate-2 会校验）

### 章节与 Gate-2 的关系

Gate-2 解析模板中的 `##` 级别标题，逐项检查产出是否包含对应章节。缺失章节或未填充占位符时输出提示。

## L3 案例开发

### 文件格式

```markdown
# 案例：案例名称

## 背景
描述问题出现的背景。

## 问题
具体的问题描述。

## 处理方法
1. 步骤一
2. 步骤二

## 结果
- 发现了什么
- 采取了什么措施

## 经验总结
- 可复用的方法论
- 需要注意的坑

## 标签
- 行业: 水务公用事业
- 场景: 分析
- 难度: 中等
- 关联规则: [L1:anm-nrw-variance]

> 案例中的数据已脱敏，不包含真实业务数据。
```

### 注意事项

- 所有数据必须脱敏
- `validate_pack.py` 会检测疑似敏感数字（16-19 位数字、手机号等）
- 案例提供方法论参考，不是强制约束
- 案例可引用 L1 规则和 L4 决策记录

## L4 决策记录

### 自动生成

AI 在每次 Gate-2 通过后自动写入，无需手动操作。

### 手动编辑

用户可随时编辑历史记录，追加备注或修正判断。

### Instinct 开发

```yaml
id: budget-variance-pipeline
trigger: "当分析预算执行偏差时"
action: "优先检查管网维护费科目"
confidence: 0.7
domain: [budget, variance]
evidence: "财务人员在 2026-07 任务中纠正了此判断"
scope: pack
created_at: "2026-08-02"
updated_at: "2026-08-02"
```

| 字段 | 说明 |
|------|------|
| `id` | 唯一标识，与文件名一致 |
| `trigger` | 触发条件描述 |
| `action` | 建议行为 |
| `confidence` | 0.3 试探 / 0.5 中等 / 0.7 强 / 0.9 核心 |
| `domain` | 领域标签数组 |
| `evidence` | 证据来源 |
| `scope` | `project`（仅当前项目）/ `pack`（整个经验包） |

## 元数据推断

无 pack.yml，元数据从文件内容推断：

| 字段 | 推断来源 | 默认值 |
|------|----------|--------|
| id | 目录名 | 目录名 |
| name | README.md 首行标题 | 目录名 |
| version | README.md 中的版本标注 | 1.0.0 |
| domain | README.md 中的领域标注 | pack-id |
| keywords | L1 core name + L1 context keywords + L3 标题 + README 关键词行 | 空 |

## 校验与安全

### 校验经验包

```bash
python tools/validate_pack.py packs/my-pack/
```

检查：
- L1-rules/ 目录存在且规则字段完整
- L2-templates/ 目录存在
- L3-cases/ 案例脱敏
- L4-decision-logs/ 目录存在
- README.md 存在且标注版本

### 安全扫描

```bash
python tools/scan_pack.py packs/my-pack/
```

检测：
- Alert：忽略上文、角色劫持、系统指令窃取、API Key 泄露
- Warn：强制指令、外部 URL、隐瞒用户指令
- Info：记忆注入、行为覆写、角色扮演

## 最佳实践

1. **core 精简**：core 规则 <=10 条，只放真正通用的规则
2. **context 聚焦**：每个 context 文件聚焦一个场景，keywords 精准
3. **模板完整**：L2 模板包含完整的任务说明、输入要求、执行步骤和产出格式
4. **案例脱敏**：L3 案例必须脱敏，用 `validate_pack.py` 检测
5. **引用显式**：L2 模板的 rules 声明使用 `[L1:core:name]` `[L1:context:name]` 显式语法
6. **定期扫描**：每次修改后运行 `scan_pack.py` 检查安全风险
