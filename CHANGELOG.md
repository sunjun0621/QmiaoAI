# 变更日志

所有版本变更记录。版本号遵循语义化版本（MAJOR.MINOR.PATCH）。

## v1.0.0 - 2026-08-02

### 架构

- 三层分离架构：引擎层 `core/` + 配置层 `packs/` + 数据层 `data-buffer/`
- 四层经验包结构：L1 规则 + L2 模板 + L3 案例 + L4 决策记录
- 纯约定扫描（无 pack.yml），元数据从文件内容推断

### 引擎层

- `SYSTEM.md`：核心系统指令，定义身份、三原则、四层经验包、七阶段流水线
- `PACK_LOADER.md`：经验包加载器，L1 两层扫描（core 全量 + context 关键词触发）、多包叠加
- `RULE_SCANNER.md`：规则扫描器，core/context 区分、5 种规则类型、Instinct 召回、evidence_chain
- `GATE.md`：两级 Gate 机制，Gate-1 数据准入（3 项）+ Gate-2 产出校验（5 项），均非阻断
- `REF_SYNTAX.md`：引用语法，8 种引用格式，L1 三层解析，跨包引用
- `REVIEWER.md`：独立审查 agent，预报告门控四问、误报清单、五维度审查
- `SYSTEM-FULL.md`：全量合并版（6 合 1）
- `VERSION.json`：版本信息

### L1 规则两层加载

- `core/`：始终加载，领域无关通用规则，<=10 条
- `context/`：关键词触发加载，领域特定规则
- `[L1:core:name]` `[L1:context:name]` 显式引用语法
- `[L1:name]` 默认语法：先查 core 再查 context
- 向后兼容：无子目录时全量加载

### Gate 机制

- Gate-1：数据格式确认、脱敏提示、技能选择（均非阻断）
- Gate-2 第一环节：L1 规则符合性、L2 模板骨架、L3 案例一致性、Instinct 召回
- Gate-2 第二环节：独立财务审查（REVIEWER）
- 两环节独立输出，互不阻断

### Instinct 直觉经验

- `L4-decision-logs/instincts/` 目录存储直觉经验卡片
- confidence 分流：>=0.7 自动应用 / 0.3-0.6 仅提示 / <0.3 静默跳过
- `[L4:instinct:name]` 引用语法
- 3 条示例 instinct 覆盖预算偏差/勾稽校验/现金流分类场景

### 经验包

- `water-soe-finance`：水务国企经验包，33 条规则（core 10 + context 23）、7 个模板、15 个案例、4 条 instinct
- `_template`：空白经验包模板，含 core/context 两层结构

### 工具脚本

- `init_pack.py`：从 _template 创建新经验包
- `validate_pack.py`：校验经验包结构和规则完整性
- `scan_pack.py`：安全扫描（prompt injection 检测，Alert/Warn/Info 三级，.gov.cn 白名单）

### 其他

- 平台适配器：千帆 + 通用
- MIT 许可证
- 三原则：数据责任归用户、用户自主可控、核心框架稳定
