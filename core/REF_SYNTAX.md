# 引用语法解析器（REF_SYNTAX）

## 作用

定义引擎层的引用语法，使 L2 模板、L3 案例、L4 决策记录和用户指令能够通过统一语法引用经验包中的规则、模板、案例和决策记录。引擎层硬编码解析，AI 按本文件规则理解并解析所有引用。

## 语法格式

```
[L{层级}:{标识符}]
```

| 语法 | 指向 | 解析目录 |
|------|------|----------|
| `[L1:core:name]` | L1 核心规则 | `packs/{pack}/L1-rules/core/` |
| `[L1:context:name]` | L1 上下文规则 | `packs/{pack}/L1-rules/context/` |
| `[L1:name]` | L1 规则（先查 core 再查 context） | `packs/{pack}/L1-rules/core/` → `context/` |
| `[L2:name]` | L2 模板 | `packs/{pack}/L2-templates/` |
| `[L3:name]` | L3 案例 | `packs/{pack}/L3-cases/` |
| `[L4:name]` | L4 决策记录 | `packs/{pack}/L4-decision-logs/` |
| `[L4:instinct:name]` | L4 Instinct | `packs/{pack}/L4-decision-logs/instincts/` |
| `[REVIEWER]` | 独立审查 agent | `core/REVIEWER.md` |

## 标识符解析规则

### L1 规则解析（两层结构）

L1 引用支持三种语法，按显式程度从高到低：

1. **显式 core 引用** `[L1:core:name]`：仅在 `L1-rules/core/` 目录下查找
2. **显式 context 引用** `[L1:context:name]`：仅在 `L1-rules/context/` 目录下查找
3. **默认引用** `[L1:name]`：先查 `core/`，再查 `context/`，命中即返回

默认引用的匹配优先级（从高到低）：

1. 文件名匹配：`name` 直接对应文件名（不含扩展名）。先在 `core/` 下查找，再在 `context/` 下查找。如 `[L1:checklist]` → 先查 `core/checklist.yml`，命中则返回；未命中再查 `context/checklist.yml`
2. 规则 id 匹配：在 YAML 规则文件中查找 `id: name` 的规则条目。先扫描 `core/` 下所有文件，再扫描 `context/` 下所有文件
3. 模糊匹配：标识符作为关键词在文件内容中搜索，返回最相关的条目

匹配失败时输出提示：`[L1:xxx] 未找到匹配项，请检查标识符`，不中断处理。

> **向后兼容**：若 `L1-rules/` 下无 `core/` 和 `context/` 子目录（旧格式），`[L1:name]` 直接在 `L1-rules/` 下查找，行为一致。

## 使用场景

### 场景一：L2 模板引用 L1 规则（声明产出约束）

L2 模板在头部声明本模板产出必须满足的 L1 规则。推荐使用显式 core/context 语法：

```markdown
---
rules: [L1:core:accounting], [L1:core:checklist], [L1:context:anomaly], [L1:context:audit], [L1:context:variance]
---

# 月度分析报告

...
```

也支持默认语法（先查 core 再查 context）：

```markdown
---
rules: [L1:accounting], [L1:checklist], [L1:anomaly], [L1:audit]
---
```

引擎解析到 `rules` 声明后，在 Gate-2 阶段优先校验这些规则。

### 场景二：L3 案例引用 L1 规则和 L4 决策

L3 案例在内容中引用相关规则和历史决策：

```markdown
## 处理方法
按 [L1:context:anm-nrw-variance] 规则检测产销差偏差，参考 [L4:2026-07-monthly-analysis] 的处置思路...
```

引擎解析后，在参考案例时同时加载关联的规则和决策记录。

### 场景三：用户指令中引用

用户在对话中直接使用引用语法：

```
按 [L2:monthly-analysis] 模板出件，重点检查 [L1:context:anm-nrw-variance]
```

引擎解析后加载指定模板和规则执行。

### 场景四：L4 决策记录引用

L4 决策记录中引用本次处理使用的规则、模板和案例：

```markdown
## 引用
规则: [L1:context:var-water-revenue-budget], [L1:context:aud-wsoe-reconciliation]
模板: [L2:monthly-analysis]
案例: [L3:case-001-water-loss]
```

L4 决策记录中的 `## 证据链` 章节记录从输入到产出的全链路证据追踪。通过 `[L4:name]` 引用决策记录时，引擎自动加载该记录的全部内容（含 evidence_chain）到处理上下文，无需独立引用语法。evidence_chain 的加载和匹配规则详见 `core/RULE_SCANNER.md` 的 "evidence_chain 证据链" 章节。

### 场景五：Instinct 引用（新增）

在 L2 模板、L3 案例或用户指令中引用特定 instinct，使引擎在处理时加载该 instinct 并按其 confidence 执行：

```markdown
## 分析要求
预算偏差分析时参考 [L4:instinct:budget-variance-pipeline]
```

引用 instinct 时引擎行为：
- 加载该 instinct 的完整 YAML 到处理上下文
- 若 confidence >= 0.7，将 action 作为建议嵌入产出
- 若 confidence < 0.7，在 Gate-2 Instinct 召回中作为提示列出
- 引用本身不改变 instinct 的 confidence 值

## 跨包引用

默认引用当前激活的经验包。如需引用其他经验包，使用扩展语法：

```
[L1:pack-id/core/name]      # 跨包引用核心规则
[L1:pack-id/context/name]   # 跨包引用上下文规则
[L1:pack-id/name]           # 跨包默认引用（先 core 再 context）
```

示例：`[L1:water-soe-finance/context/anomaly]` 引用 water-soe-finance 经验包中的 context/anomaly.yml。

## 解析流程

```
1. 扫描文本中的 [L{1-4}:{identifier}] 模式，含 [L4:instinct:{identifier}] 子模式
2. 扫描文本中的 [REVIEWER] 标记（无参数，直接引用审查 agent 行为规则）
3. 对 L1 引用，按以下顺序解析标识符：
   a. [L1:core:name]  → 仅在 L1-rules/core/ 目录下查找
   b. [L1:context:name] → 仅在 L1-rules/context/ 目录下查找
   c. [L1:name]       → 先查 L1-rules/core/，再查 L1-rules/context/（向后兼容：无子目录时直接查 L1-rules/）
4. 确定当前激活的经验包
5. 按标识符匹配优先级查找目标（文件名 → 规则 id → 模糊匹配）
6. 匹配成功 → 加载内容到处理上下文
7. 匹配失败 → 输出提示，继续处理
8. 跨包引用 → 切换到指定经验包目录查找
9. [L4:instinct:name] → 在 L4-decision-logs/instincts/ 目录下按文件名匹配 {name}.yml
10. [REVIEWER] → 加载 core/REVIEWER.md 中的审查行为规则到 Gate-2 第二环节上下文
```

## 注意事项

- 引用语法是引擎层能力，所有经验包通用
- 引用不改变 Gate 的非阻断特性
- 同一标识符可被多次引用，内容只加载一次
- L4 引用是只读的，不会触发 L4 记录的写入
- `[L4:instinct:name]` 是 `[L4:name]` 的子路径语法，解析到 instincts/ 子目录而非 L4-decision-logs/ 根目录
- instinct 引用不影响 instinct 的 confidence，confidence 分流规则由 RULE_SCANNER 的 Instinct 召回流程统一处理
- `[REVIEWER]` 是引擎层引用，指向 `core/REVIEWER.md`，不依赖经验包——所有经验包共享同一审查 agent 行为规则
- `[REVIEWER]` 无参数，不需要标识符，引用即加载完整审查行为规则
- `## 证据链` 是 L4 决策记录的内部章节，不使用独立引用语法，通过 `[L4:name]` 引用记录时全量加载
- `[L1:core:name]` 和 `[L1:context:name]` 是 新增的显式语法，推荐在 L2 模板 rules 声明中使用
- `[L1:name]` 默认语法保持向后兼容：有 core/context 子目录时先查 core 再查 context，无子目录时直接查 L1-rules/
