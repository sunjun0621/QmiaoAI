# 规则扫描器（RULE_SCANNER）v1.0.0

## 作用

任务执行完成后，加载当前经验包 L1 规则（core 全部 + context 按关键词命中的文件）和 L4-decision-logs/ 中的历史决策记录，逐条扫描产出内容，生成提示清单。

## 扫描流程

```
1. 读取当前经验包的 L1-rules/ 目录
2. 加载 L1-rules/core/ 下所有 .yml 规则文件（始终加载）
3. 加载 L1-rules/context/ 下用户输入命中的 .yml 规则文件（按需加载）
   a. 若无 context/ 子目录（旧格式），全量加载 L1-rules/ 下的 .yml 文件
4. 解析 L4-decision-logs/ 中的历史决策（作为参考，不作为硬约束）
5. 逐条解析规则，按类型执行匹配
6. 收集所有命中的规则，生成提示列表
7. 按 severity 排序：Alert > Warn > Info
8. 输出提示清单（附加到产出末尾）
```

## core 规则与 context 规则的区分

| 维度 | core 规则 | context 规则 |
|------|----------|-------------|
| 加载来源 | `L1-rules/core/*.yml` | `L1-rules/context/*.yml`（仅命中的文件） |
| 加载时机 | 始终加载 | 关键词命中时加载 |
| 来源标注 | `L1-rules/core/{file}.yml#{rule-id}` | `L1-rules/context/{file}.yml#{rule-id}`（按需加载） |
| 适用场景 | 领域无关通用检查 | 领域特定检查 |

提示输出中，context 规则标注"按需加载"来源，方便用户识别该规则因关键词命中而参与扫描：

```
[Warn] 产销差率 21.15%，超 15% 阈值
  规则来源：L1-rules/context/anomaly.yml#anm-nrw-variance（按需加载）
```

core 规则不标注"按需加载"：

```
[Alert] 产出中可能包含敏感信息，请确认已脱敏
  规则来源：L1-rules/core/checklist.yml#cls-desensitize
```

## 规则类型

### 数值比较型

```yaml
- id: variance-check
  name: 预算执行偏差>10%
  rule: "abs(实际-预算)/预算 > 0.10"
  severity: warn
  message: "{item}预算执行偏差{ratio}，超10%阈值"
  variables:
    item: "从上下文提取科目名称"
    ratio: "计算偏差比例"
```

### 文本匹配型

```yaml
- id: desensitize-reminder
  name: 产出包含敏感信息
  rule: "output.contains('银行账号') or output.contains('身份证号')"
  severity: alert
  message: "产出中可能包含敏感信息，请确认已脱敏"
```

### 勾稽校验型

```yaml
- id: reconciliation
  name: 收入-成本-费用=利润
  rule: "收入 - 成本 - 费用 == 利润"
  severity: warn
  message: "勾稽关系不平衡，差额{diff}，请核查"
  variables:
    diff: "计算差额"
```

### 模板引用型（新增）

规则通过引用语法声明与模板的关联：

```yaml
- id: template-conformity
  name: 产出符合模板骨架
  rule: "conforms_to([L2:monthly-report])"
  severity: warn
  message: "产出缺少模板要求的章节：{missing_sections}"
  variables:
    missing_sections: "缺失的章节列表"
```

### 自定义逻辑型

```yaml
- id: custom-check
  name: 用户自定义检查
  rule: "由用户在经验包中定义"
  severity: info
  message: "自定义提示内容"
```

## 提示输出格式

```
─── 规则扫描结果（共 3 条提示）───

[Alert] 产出中可能包含敏感信息（检测到疑似银行账号格式），请确认已脱敏
  规则来源：L1-rules/core/checklist.yml#cls-desensitize

[Warn] 勾稽关系：供水量-售水量-漏损量=产销差量，差额 5，请核查
  规则来源：L1-rules/context/audit.yml#aud-wsoe-reconciliation（按需加载）

[Warn] 产销差率 21.15%，超 15% 阈值
  规则来源：L1-rules/context/anomaly.yml#anm-nrw-variance（按需加载）
```

## L4 决策记录参考

规则扫描时，同时读取 L4-decision-logs/ 中的历史决策记录，用于：

- 识别同类问题的历史处置方式
- 提示用户"上次类似情况的处理方案"
- 避免重复提示已知并已接受的异常

L4 参考提示格式：

```
[Info] 历史参考：2026-07-15 曾处理类似问题，当时判断为 seasonal-variance，未做调整
  决策来源：L4-decision-logs/2026-07-15-budget-anomaly.md
```

### evidence_chain 证据链（新增）

L4 决策记录新增 `## 证据链` 章节，记录从输入数据到最终产出的全链路证据追踪。规则扫描时加载 evidence_chain 用于：

- 对比当前任务与历史任务的输入数据特征，判断是否为同类问题
- 参考历史 AI 推理步骤，保持分析口径一致性
- 检查当前产出结论是否与历史产出摘要方向一致
- 复用历史校验结果，避免重复提示已确认接受的异常

#### evidence_chain 结构

每条 L4 决策记录的 `## 证据链` 章节包含 6 个子节：

| 子节 | 内容 | 扫描时的用途 |
|------|------|-------------|
| 输入数据快照 | 数据来源、数据摘要（脱敏）、Gate-1 校验状态 | 判断当前输入与历史输入是否同类 |
| 规则命中记录 | 每条 L1 规则的命中/未命中状态及详情 | 对比当前规则命中情况，发现差异 |
| AI 推理步骤 | 处理过程中的关键计算和分析步骤 | 参考历史推理路径，保持口径一致 |
| 产出内容摘要 | 产出类型、关键结论、产出位置 | 检查当前结论是否与历史方向一致 |
| 校验结果 | Gate-2 规则/模板/审查的校验结论 | 复用历史已确认的校验状态 |
| 最终确认 | 用户确认状态和修改记录 | 判断异常是否已被用户接受 |

#### 加载流程

```
1. 读取 L4-decision-logs/ 目录下所有 .md 文件（不含 instincts/ 子目录）
2. 解析每条记录的 ## 证据链 章节
3. 提取输入数据快照中的数据摘要关键词
4. 提取规则命中记录中的命中规则列表
5. 与当前任务的 L1 规则命中结果做交集匹配
6. 交集非空 → 加载该记录的 evidence_chain 到参考上下文
7. 交集为空 → 跳过该记录（无规则重叠，参考价值低）
```

#### 引用方式

evidence_chain 是 L4 决策记录的内部章节，不使用独立的引用语法。通过 `[L4:name]` 引用决策记录时，引擎自动加载该记录的全部内容（含 evidence_chain）到处理上下文。

引擎加载 evidence_chain 后的参考提示格式：

```
[Info] 历史证据链参考：2026-07-monthly-analysis 曾处理同类问题
  输入特征：水务月度数据，产销差率超阈值
  规则命中：nrw-variance, operating-cost-ratio, depreciation-asset-match
  历史推理：产销差率→成本占收比→折旧率→借款利率→补贴确认
  历史结论：产销差异常+成本上升双重影响，建议管网检漏
  用户确认：已确认（曾修正营业利润勾稽错误）
  决策来源：L4-decision-logs/2026-07-monthly-analysis.md
```

#### 与 Instinct 的关系

| 维度 | evidence_chain | Instinct |
|------|----------------|----------|
| 存储位置 | L4-decision-logs/*.md 的 `## 证据链` 章节 | L4-decision-logs/instincts/*.yml |
| 数据形态 | Markdown 结构化文本 | YAML 键值对 |
| 生成时机 | 每次任务完成后自动记录 | 用户纠正 AI 判断时提取，或手动创建 |
| 加载方式 | `[L4:name]` 引用时全量加载 | domain + trigger 匹配后加载 |
| 作用 | 全链路证据追踪和历史参考 | 单点直觉经验召回 |
| 粒度 | 完整任务级别 | 单条经验卡片级别 |

evidence_chain 和 Instinct 互补：evidence_chain 提供完整的历史任务上下文，Instinct 提供从历史任务中提炼的精炼经验。规则扫描时两者独立加载，各自输出参考提示。

## Instinct 召回（新增）

规则扫描完成后，引擎扫描 L4-decision-logs/instincts/ 目录下的所有 instinct YAML 文件，按 domain 和 trigger 匹配当前任务上下文，将命中的 instinct 作为参考附加到产出末尾。

### Instinct 结构

```yaml
id: budget-variance-pipeline       # 唯一标识
trigger: "当分析预算执行偏差时"       # 触发条件
action: "优先检查管网维护费科目"      # 建议行为
confidence: 0.7                     # 置信度
domain: [budget, variance]          # 领域标签
evidence: "来源说明"                 # 证据来源
scope: pack                         # 作用域 project / pack
created_at: "2026-08-02"
updated_at: "2026-08-02"
```

### 召回流程

```
1. 读取 L4-decision-logs/instincts/ 目录下所有 .yml 文件
2. 提取当前任务的 domain 上下文（从 L1 规则命中的 domain 字段 + 产出内容关键词推断）
3. 逐条匹配 instinct：
   a. domain 交集匹配——instinct.domain 与当前任务 domain 有交集
   b. trigger 语义匹配——instinct.trigger 描述的场景与当前任务类型相关
4. 收集命中的 instinct，按 confidence 降序排列
5. 按置信度分流处理
6. 输出到产出末尾
```

### 置信度分流规则

| confidence | 处理方式 | 输出标注 |
|------------|----------|----------|
| >= 0.7 | 自动应用，将 action 内容嵌入产出建议，标注来源 | `[Instinct·Auto]` |
| 0.3 - 0.6 | 仅提示，列出 trigger 和 action 供用户参考，不自动嵌入 | `[Instinct·Hint]` |
| < 0.3 | 不输出（静默跳过） | 无 |

### 输出格式

```
─── Instinct 召回（共 2 条命中）───

[Instinct·Auto] 预算偏差分析：优先检查管网维护费科目，该科目历史偏差率高
  来源：[L4:instinct:budget-variance-pipeline] | confidence: 0.7

[Instinct·Hint] 勾稽校验：先核对折旧科目，折旧计提不足是最常见的不平原因
  来源：[L4:instinct:reconciliation-depreciation-first] | confidence: 0.9
  状态：仅提示，未自动应用（需用户确认）
```

> 注意：confidence >= 0.7 的 instinct 虽然自动应用，但仍为非阻断式——只是将建议嵌入产出，不会因 instinct 未被采纳而阻断交付。

### Instinct 生命周期

- 自动生成：Gate-2 校验中如果用户纠正了 AI 的判断，AI 可提取该纠正为 instinct 并写入 instincts/ 目录
- 手动创建：用户可直接在 instincts/ 目录下新增 .yml 文件
- 更新：用户可手动编辑 instinct 的 confidence、action 等字段
- 失效：将 confidence 降至 0.3 以下可静默停用，无需删除文件

## 注意事项

- 所有提示均为**非阻断式**，不影响交付
- 规则匹配失败（如变量缺失、表达式错误）时输出 Info 级提示，不中断扫描
- 无经验包加载时跳过扫描，产出直接交付
- L4 决策记录作为参考信息，不作为硬约束阻断产出
- 规则扫描结果同时供 Gate-2 使用，Gate-2 在此基础上增加模板骨架和案例一致性校验
