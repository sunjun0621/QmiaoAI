# 版本迁移指南

> 本文档说明各版本间的迁移步骤和兼容性说明。

## 迁移到 v4.3（L1 两层拆分）

### 变更概述

v4.3 将 L1 规则从全量加载改为两层加载：`core/`（始终加载）+ `context/`（关键词触发）。

### 自动迁移

如果你的经验包使用旧格式（`L1-rules/` 下直接有 `.yml` 文件，无 `core/` 和 `context/` 子目录），引擎会自动全量加载，行为与 v4.2 一致。你不需要立即迁移。

### 手动迁移步骤

1. 创建子目录：

```bash
mkdir -p packs/my-pack/L1-rules/core
mkdir -p packs/my-pack/L1-rules/context
```

2. 将领域无关的通用规则（会计恒等式、脱敏检查、格式规范等，<=10 条）移到 `core/`：

```bash
mv packs/my-pack/L1-rules/accounting.yml packs/my-pack/L1-rules/core/
mv packs/my-pack/L1-rules/checklist.yml packs/my-pack/L1-rules/core/
```

3. 将领域特定规则移到 `context/`，并为每个文件添加 `keywords` 字段：

```yaml
# 在文件头添加 keywords
keywords: [偏差, 异常, 波动, 产销差]
```

4. 更新 L2 模板中的引用语法：

```markdown
# 旧语法（仍然有效）
rules: [L1:accounting], [L1:checklist], [L1:anomaly]

# 新语法（推荐，显式指定）
rules: [L1:core:accounting], [L1:core:checklist], [L1:context:anomaly]
```

5. 更新经验包 README.md 中的规则概要描述。

6. 运行校验：

```bash
python tools/validate_pack.py packs/my-pack/
```

### 兼容性

- `[L1:name]` 默认语法保持兼容：有 core/context 时先查 core 再查 context
- 旧格式（无子目录）自动全量加载，引擎会提示升级
- 引擎检测到旧格式时提示用户升级到两层结构

## 迁移到 v4.2（REVIEWER）

### 变更概述

v4.2 新增独立审查 agent（REVIEWER），Gate-2 从单一环节拆分为规则扫描 + 独立审查两个环节。

### 迁移步骤

1. 更新引擎：加载新的 `core/REVIEWER.md`
2. 无需修改经验包：REVIEWER 是引擎层能力，不依赖经验包配置
3. Gate-2 输出新增第二区块（独立审查报告），原有规则扫描结果不变

### 兼容性

- 经验包无需任何修改
- Gate-2 原有 4 项校验不变，新增第 5 项（独立审查）

## 迁移到 v4.1（Instinct）

### 变更概述

v4.1 新增 Instinct 直觉经验召回机制。

### 迁移步骤

1. 创建 instincts 目录（可选）：

```bash
mkdir -p packs/my-pack/L4-decision-logs/instincts
```

2. 按需创建 instinct YAML 文件（参考 `instinct-template.yml`）

### 兼容性

- Instinct 是可选功能，不创建 instincts 目录不影响使用
- Gate-2 新增第 4 项校验（Instinct 召回），无 instinct 文件时自动跳过

## 迁移到 v4.0（三层分离架构）

### 变更概述

v4.0 是架构重构版本，引入三层分离、四层经验包、两级 Gate、引用语法。

### 从 v3 迁移

v3 使用多级审批流和 pack.yml，v4 完全重构：

1. 将原有规则文件按 L1-L4 分类重新组织
2. 删除 pack.yml，改为纯约定扫描
3. 更新引擎指令为 v4 的 5 个文件
4. 运行 `validate_pack.py` 校验

### 兼容性

- v4.0 是不兼容变更，v3 经验包需要手动迁移
- 最低兼容版本 `>=4.0.0`
