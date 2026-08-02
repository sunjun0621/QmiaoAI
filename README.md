# 钱喵 AI 财务助手

> v4.3.0 | MIT License | 2026-08-02

一个面向国企财务人员的 AI 辅助系统。不是替代人做判断，而是像一个经验丰富的同事：帮忙干活、检查产出、善意提醒。

## 它解决什么问题

财务人员日常面对大量重复性工作：月度分析报告、经济效益月报、年度决算、专项分析、报表编制。这些工作有固定模板和规则约束，但每次都要手工填写、逐项核对、交叉勾稽。钱喵把这些模板和规则固化进 AI，让 AI 按规矩出件、按规则检查、按案例参考。

## 核心架构：三层分离

| 层 | 目录 | 归属 | 特性 |
|----|------|------|------|
| 引擎层 | `core/` | 不可变 | 领域无关的系统指令，7 个文件驱动全部行为 |
| 配置层 | `packs/` | 用户拥有 | 四层经验包（L1-L4），可替换、可升级、可 DIY |
| 数据层 | `data-buffer/` | 即用即弃 | 用户脱敏数据入口和产出结果，全部 .gitignore |

引擎不包含任何业务知识，所有行业规则、报告模板、历史案例都放在用户拥有的经验包中。换一个经验包，同一个引擎就能服务不同行业。

## 三原则

1. **数据责任归用户**：数据来源、脱敏、安全由使用者全权负责，AI 不拥有、不修改、不存储用户数据
2. **用户自主可控**：经验包可自由增删改，越用越贴合用户领域
3. **核心框架稳定**：AI 严格按规则办事、按模板出件、按案例参考，两级 Gate 校验产出合规性，但所有校验均为提示式，不阻断交付

## 快速开始

### 30 秒理解

```
core/        ← 引擎，7 个 .md 文件定义全部行为，不碰业务数据
packs/       ← 经验包，用户拥有，放规则/模板/案例/决策记录
data-buffer/ ← 数据层，你的脱敏数据进 input/，AI 产出写 output/
tools/       ← 3 个 Python 工具：初始化/校验/安全扫描经验包
adapters/    ← 平台适配器，告诉你在不同 AI 平台上怎么加载
```

### 加载到 AI 平台

1. 按顺序拼接以下 5 个文件（或直接用 `core/SYSTEM-FULL.md`，它已包含全部）：
   - `core/SYSTEM.md`
   - `core/PACK_LOADER.md`
   - `core/RULE_SCANNER.md`
   - `core/GATE.md`
   - `core/REF_SYNTAX.md`

2. 拼接内容粘贴到 AI 平台的系统指令区域

3. 经验包内容（L1-L4）上传到知识库或粘贴到对话中

4. 对 AI 说："你是谁？" 预期回答包含"钱喵"和"AI 财务助手"

详见 `adapters/` 下的平台适配器说明。

### 首次使用

```bash
# 校验已有经验包
python tools/validate_pack.py packs/water-soe-finance/

# 安全扫描经验包（检测 prompt injection）
python tools/scan_pack.py --all

# 创建新经验包
python tools/init_pack.py my-pack "我的经验包"
```

### 使用已有经验包

将脱敏数据放入 `data-buffer/input/`，对 AI 说：

- "用水务经验包分析这个月的产销差数据"
- "分析本月水费收入预算执行情况"
- "看看这个季度的运营成本有没有异常"

## 内置经验包

| 经验包 | 领域 | L1 规则 | L2 模板 | L3 案例 |
|--------|------|---------|---------|---------|
| `water-soe-finance` | 水务国企 | 33 条（core 10 + context 23） | 7 个 | 15 个 |
| `_template` | 空白模板 | 示例规则 | 1 个 | 1 个 |

## 引擎处理流水线

```
数据接入 → Gate-1 数据准入 → 规则预扫描 → AI 处理 → 审计执行 → Gate-2 产出校验 → 产出 output/
                                                                              ↓
                                                                        L4 自动记录
```

- **Gate-1**：数据格式确认、脱敏提示、技能选择（均非阻断）
- **Gate-2**：规则扫描（L1/L2/L3/Instinct）+ 独立审查（REVIEWER），两个环节独立输出

## 四层经验包

| 层 | 目录 | 内容 | 格式 |
|----|------|------|------|
| L1 规则 | `L1-rules/` | 公式、阈值、政策法规 | YAML |
| L2 模板 | `L2-templates/` | 报告骨架、任务流程 | Markdown |
| L3 案例 | `L3-cases/` | 历史处理经验 | Markdown |
| L4 决策 | `L4-decision-logs/` | AI 自动记录的决策留痕 + 直觉经验卡片 | Markdown + YAML |

L1 规则从 v4.3 起拆分为 core（始终加载，<=10 条领域无关规则）和 context（关键词触发加载，领域特定规则），解决全量加载导致的上下文膨胀。

## 技术栈

- 纯 Markdown + YAML，无运行时依赖
- Python 工具脚本（仅用于经验包管理，不参与运行时）
- 兼容任何支持系统指令的 AI 平台

## 项目结构

```
qianxiaomiao-finance/
├── core/                  # 引擎层（7 文件）
│   ├── SYSTEM.md          # 核心系统指令
│   ├── SYSTEM-FULL.md     # 全量合并版（5 合 1）
│   ├── PACK_LOADER.md     # 经验包加载器
│   ├── RULE_SCANNER.md    # 规则扫描器
│   ├── GATE.md            # 两级 Gate 机制
│   ├── REF_SYNTAX.md      # 引用语法
│   ├── REVIEWER.md        # 独立审查 agent
│   └── VERSION.json       # 版本信息
├── packs/                 # 配置层
│   ├── water-soe-finance/ # 水务国企经验包
│   └── _template/         # 空白模板
├── data-buffer/           # 数据层
│   ├── input/             # 用户数据入口
│   ├── output/            # AI 产出
│   └── templates/         # 数据模板
├── tools/                 # 工具脚本
│   ├── init_pack.py       # 创建经验包
│   ├── validate_pack.py   # 校验经验包
│   └── scan_pack.py       # 安全扫描
├── adapters/              # 平台适配器
├── docs/                  # 文档
├── .gitignore
├── LICENSE
├── README.md
├── SPEC.md
├── CHANGELOG.md
├── CONTRIBUTING.md
└── CODE_OF_CONDUCT.md
```

## 版本历史

| 版本 | 日期 | 核心变更 |
|------|------|----------|
| v4.3 | 2026-08-02 | L1 规则两层拆分（core 始终加载 + context 关键词触发） |
| v4.2 | 2026-08-01 | 新增独立审查 agent（REVIEWER），Gate-2 拆分为两环节 |
| v4.1 | 2026-08-01 | 新增 Instinct 直觉经验召回机制 |
| v4.0 | 2026-07-31 | 三层分离架构（引擎/配置/数据），两级 Gate，引用语法 |

详见 `CHANGELOG.md`。

## 许可证

MIT License - 详见 `LICENSE`

## 相关文档

- `SPEC.md` - 技术规格说明书
- `docs/architecture.md` - 架构详解
- `docs/getting-started.md` - 快速上手指南
- `docs/pack-development.md` - 经验包开发指南
- `docs/migration-guide.md` - 版本迁移指南
- `docs/roadmap.md` - 路线图
