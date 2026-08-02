# 经验包模板

> 版本：1.0.0 | 用途：新经验包的起始模板

## 概述

这是创建新经验包的空白模板。使用 `tools/init_pack.py` 从本模板创建新经验包：

```bash
python tools/init_pack.py my-pack "我的经验包名称"
```

## 目录结构

```
_template/
├── README.md                          ← 本文件
├── L1-rules/
│   ├── core/                          # 核心规则（始终加载，<=10 条）
│   │   ├── accounting.yml             # 会计核算通用规则模板
│   │   └── checklist.yml              # 通用自检清单模板
│   └── context/                       # 上下文规则（关键词触发）
│       ├── anomaly.yml                # 异常阈值模板
│       ├── audit.yml                  # 审计规则模板
│       └── variance.yml               # 预算执行模板
├── L2-templates/
│   └── monthly-analysis.md            # 月度分析模板
├── L3-cases/
│   └── case-template.md               # 案例模板
└── L4-decision-logs/
    ├── .gitkeep
    └── decision-template.md           # 决策记录模板
```

## 开发步骤

1. 从模板创建经验包：`python tools/init_pack.py <pack-id> "<pack-name>"`
2. 编辑 `L1-rules/core/` 下的规则文件，定义领域无关的通用规则（<=10 条）
3. 编辑 `L1-rules/context/` 下的规则文件，添加 `keywords` 字段，定义领域特定规则
4. 编辑 `L2-templates/` 下的模板文件，定义产出格式和任务流程
5. 创建 `L3-cases/` 案例（可选）
6. 创建 `L4-decision-logs/instincts/` 直觉经验卡片（可选）
7. 更新本 README.md，标注版本和领域
8. 运行校验：`python tools/validate_pack.py packs/<pack-id>/`
9. 运行安全扫描：`python tools/scan_pack.py packs/<pack-id>/`

## 规则文件格式

详见 `docs/pack-development.md`。

## 模板文件格式

详见 `docs/pack-development.md` 的 L2 模板开发部分。
