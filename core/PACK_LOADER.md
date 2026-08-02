# 经验包加载器（PACK_LOADER）v4.3

## 作用

启动时扫描 `packs/` 目录，通过**纯约定扫描**（无 pack.yml）加载所有经验包，注册到内存中的经验包清单。L1 规则采用两层加载机制（core 始终加载 + context 按关键词触发）。

## 纯约定扫描

v4.0 去掉了 pack.yml，改为目录约定扫描。引擎自动识别经验包结构和元数据。v4.3 新增 L1 两层拆分。

### 扫描流程

```
1. 扫描 packs/ 目录下的子目录（_template 除外）
2. 每个子目录即一个经验包，目录名 = pack-id
3. 检查子目录中是否存在 L1-rules/ L2-templates/ L3-cases/ L4-decision-logs/ 四个目录
4. 至少包含 L1-rules/ 或 L2-templates/ 之一才视为有效经验包
5. 扫描 L1-rules/ 目录结构：
   a. 若存在 L1-rules/core/ 子目录 → 全量加载 core/ 下所有 .yml 文件（始终加载）
   b. 若存在 L1-rules/context/ 子目录 → 解析每个 .yml 文件头的 keywords 字段，注册到关键词清单
   c. 若 L1-rules/ 下直接有 .yml 文件（无 core/context 子目录，旧格式）→ 全量加载（向后兼容）
6. 从文件内容推断元数据（名称、关键词、版本、领域）
7. 注册到经验包清单（内存）
8. 输出已加载经验包摘要
```

### 目录结构约定

```
packs/{pack-id}/
├── L1-rules/
│   ├── core/              # 核心规则（始终加载，领域无关）
│   │   ├── accounting.yml  # 会计恒等式、借贷平衡等通用规则
│   │   └── checklist.yml   # 通用自检清单（脱敏、格式等）
│   └── context/           # 上下文规则（关键词触发加载，领域特定）
│       ├── anomaly.yml     # 异常阈值（keywords: 偏差、异常、波动...）
│       ├── audit.yml       # 审计规则（keywords: 勾稽、审计、校验...）
│       └── variance.yml    # 预算执行（keywords: 预算、执行率...）
├── L2-templates/      # 模板库（Markdown，含任务流程）
├── L3-cases/          # 案例库（Markdown）
├── L4-decision-logs/  # 决策记录（Markdown，AI 自动写入）
└── README.md          # 经验包说明（可选，用于推断元数据）
```

### L1 两层加载机制（v4.3 新增）

L1 规则拆分为 core 和 context 两层，解决全量加载导致的上下文膨胀问题：

| 层 | 目录 | 加载时机 | 规则特点 | 数量约束 |
|----|------|----------|----------|----------|
| core | `L1-rules/core/` | **始终加载** | 领域无关通用规则（会计恒等式、脱敏检查、格式规范） | <=10 条 |
| context | `L1-rules/context/` | **关键词命中时加载** | 领域特定规则（水务阈值、特定科目校验等） | 无限制 |

#### core 规则

- 扫描 `L1-rules/core/` 下所有 `.yml` 文件，全量加载到处理上下文
- 规则数量控制在 10 条以内，确保始终加载不会显著膨胀上下文
- 放置领域无关的通用规则：会计恒等式、借贷平衡、脱敏检查、格式规范

#### context 规则

- 扫描 `L1-rules/context/` 下所有 `.yml` 文件，解析文件头的 `keywords` 字段
- 将每个文件的 keywords 注册到内存中的关键词清单：

```yaml
context_keyword_registry:
  - file: anomaly.yml
    keywords: [偏差, 异常, 波动, 产销差, 水费, 成本, 回收率, 同比, 环比, 变动]
  - file: audit.yml
    keywords: [勾稽, 审计, 校验, 折旧, 借款, 利息, 补贴, 报表, 平衡]
  - file: variance.yml
    keywords: [预算, 执行率, 偏差, 预算执行, 预算偏差, 资本性支出, capex]
```

- 用户输入命中某文件的关键词时，加载该文件的所有规则
- 多个 context 文件可同时加载（如用户输入同时命中 anomaly 和 audit 的关键词）
- context 文件未命中关键词时不加载，不占用上下文

#### context 文件格式要求

每个 context YAML 文件必须在文件头声明 `keywords` 字段：

```yaml
# L1 上下文规则 - 异常阈值
keywords: [偏差, 异常, 波动, 产销差, 水费]

checks:
  - id: nrw-variance
    name: 产销差率超阈值
    ...
```

#### 向后兼容

若 `L1-rules/` 下直接有 `.yml` 文件（无 `core/` 和 `context/` 子目录），视为旧格式，全量加载所有规则。引擎检测到旧格式时提示用户升级到两层结构。

### 元数据推断规则

无 pack.yml 后，元数据从文件内容推断：

| 字段 | 推断来源 | 默认值 |
|------|----------|--------|
| id | 目录名 | 目录名 |
| name | README.md 首行标题 | 目录名 |
| version | README.md 中的版本标注，或 `1.0.0` | `1.0.0` |
| domain | README.md 中的领域标注 | pack-id |
| keywords | 扫描 L1 core 规则 name 字段 + L1 context 文件 keywords + L3 案例标题 + README.md 关键词行 | 空 |
| compatibility | 默认兼容 `>=4.0.0` | `>=4.0.0` |

## 触发机制

用户输入时，核心引擎执行两级关键词匹配：

### 第一级：经验包匹配

扫描已加载经验包的 `keywords`：

- 关键词命中 → 激活该经验包
- 多包命中 → 提示用户选择，或按加载顺序取第一个
- 无命中 → 通用模式执行（无经验包约束）
- 显式指定 → 用户说"用水务经验包"直接加载

### 第二级：L1 context 规则匹配

经验包激活后，扫描该经验包的 `context_keyword_registry`：

- 用户输入命中某 context 文件的 keywords → 加载该文件的所有规则
- 多个 context 文件命中 → 同时加载（如 anomaly + audit 同时命中）
- 无 context 文件命中 → 仅加载 core 规则
- 用户显式指定 → "[L1:context:anomaly]" 直接加载指定文件

### 加载结果

每次任务加载的 L1 规则 = core 全部 + context 命中文件。Gate-1 输出中显示完整加载清单。

## 多包叠加规则

| 层 | 叠加规则 |
|----|----------|
| L1 core 规则 | 后加载覆盖先加载（同名规则 id 以后者为准） |
| L1 context 规则 | 各包独立维护关键词清单，命中后独立加载；同名规则 id 以后加载包为准 |
| L2 模板 | 后加载覆盖先加载（同名文件名以后者为准） |
| L3 案例 | 合并，不覆盖（所有案例都保留） |
| L4 决策记录 | 不叠加，各包独立维护 |

冲突时 AI 提示用户："检测到多个经验包包含规则 [L1:xxx]，已使用 Y 包的版本，如需切换请指定。"

## 经验包清单格式

加载完成后，内存中维护如下清单：

```yaml
loaded_packs:
  - id: water-soe-finance
    name: 水务国企财务经验包
    version: 1.1.0
    domain: water-utility
    keywords: [产销差, 水费回收, 管网, 污水, 预算执行]
    L1_core_count: 10
    L1_context_count: 23
    L1_context_files:
      - file: anomaly.yml
        keywords: [偏差, 异常, 波动, 产销差, 水费, 成本, 回收率, 同比, 环比, 变动]
      - file: audit.yml
        keywords: [勾稽, 审计, 校验, 折旧, 借款, 利息, 补贴, 报表, 平衡]
      - file: variance.yml
        keywords: [预算, 执行率, 偏差, 预算执行, 预算偏差, 资本性支出, capex]
    L2_templates_count: 7
    L3_cases_count: 15
    L4_logs_count: 2
    path: packs/water-soe-finance/
  - id: _template
    name: 空白模板
    status: inactive
```

## 卸载经验包

用户可随时说"卸载水务经验包"，核心引擎从内存清单中移除该包，不再匹配其关键词和规则。

## 经验沉淀

用户可手动将处理过程沉淀为 L3 案例：
1. 用户说"把这个案例存下来"
2. AI 协助提取关键信息（背景、问题、处理方法、结果、经验）
3. 用户确认后存入当前经验包的 `L3-cases/` 目录

L4 决策记录由 AI 在每次 Gate-2 通过后自动写入，无需用户手动操作。
