# 版本迁移指南

> 本文档说明版本间的迁移步骤和兼容性说明。

## v1.0 经验包规范

### L1 规则两层结构

经验包的 L1 规则使用 core/context 两层结构：

```
L1-rules/
├── core/              # 核心规则（始终加载，<=10 条）
│   ├── accounting.yml
│   └── checklist.yml
└── context/           # 上下文规则（关键词触发）
    ├── anomaly.yml
    ├── audit.yml
    └── variance.yml
```

### 创建新经验包

```bash
python tools/init_pack.py my-pack "我的经验包"
```

从 `_template` 创建完整的四层目录结构。

### 从外部格式迁移

如果你有已有的规则文件（非本项目格式），按以下步骤迁移：

1. 创建经验包目录结构：

```bash
python tools/init_pack.py my-pack "我的经验包"
```

2. 将领域无关的通用规则（会计恒等式、脱敏检查等，<=10 条）编写为 YAML，放入 `L1-rules/core/`

3. 将领域特定规则放入 `L1-rules/context/`，每个文件添加 `keywords` 字段：

```yaml
keywords: [偏差, 异常, 波动, 产销差]
```

4. 将报告模板放入 `L2-templates/`，头部声明引用的 L1 规则

5. 将脱敏后的案例放入 `L3-cases/`

6. 运行校验：

```bash
python tools/validate_pack.py packs/my-pack/
python tools/scan_pack.py packs/my-pack/
```

### 兼容性说明

- 最低引擎版本：`>=1.0.0`
- 无 `core/context` 子目录时，`L1-rules/` 下的 `.yml` 文件自动全量加载
- `[L1:name]` 默认语法：有 core/context 时先查 core 再查 context，无子目录时直接查 `L1-rules/`
- 平台无关：任何支持系统指令的 AI 平台均可使用
