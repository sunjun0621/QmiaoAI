# 变更日志

所有版本变更记录。版本号遵循语义化版本（MAJOR.MINOR.PATCH）。

## v4.3.0 - 2026-08-02

### 新增

- L1 规则两层拆分：`core/`（始终加载，领域无关通用规则，<=10 条）+ `context/`（关键词触发加载，领域特定规则）
- `PACK_LOADER` 新增 L1 两层扫描逻辑：core 全量加载，context 注册关键词清单并按命中加载
- `RULE_SCANNER` 区分 core/context 规则扫描范围，context 规则标注"按需加载"来源
- `GATE-1` 输出显示"本次加载规则：core(全部) + context(命中的文件列表)"
- `REF_SYNTAX` 新增 `[L1:core:name]` `[L1:context:name]` 引用语法，`[L1:name]` 默认先查 core 再查 context

### 变更

- water-soe-finance 经验包 33 条规则完成 core/context 拆分：core 10 条（accounting 8 + checklist 2）+ context 23 条（anomaly 10 + audit 11 + variance 2）
- _template 经验包同步调整为 core/context 两层结构
- L2 模板 7 个文件 19 处引用同步更新为显式 core/context 语法

### 向后兼容

- 无 `core/` 和 `context/` 子目录时，全量加载 `L1-rules/` 下的 `.yml` 文件（与 v4.2 行为一致）
- `[L1:name]` 默认语法保持向后兼容

## v4.2.0 - 2026-08-01

### 新增

- 独立财务审查 agent（REVIEWER），定义在 `core/REVIEWER.md`
- Gate-2 拆分为规则扫描 + 独立审查两个独立环节
- 预报告门控四问（位置、错误模式、规则对照、严重性）
- 常见误报清单（6 项必须跳过的主观建议类型）
- 五维度审查范围（L1 规则、L2 模板、L3 案例、勾稽关系、敏感信息）

### 变更

- Gate-2 校验项从 4 项增至 5 项，第 5 项为独立财务审查
- 规则扫描和独立审查独立输出，互不阻断

## v4.1.0 - 2026-08-01

### 新增

- Instinct 直觉经验卡片机制（`L4-decision-logs/instincts/`）
- `RULE_SCANNER` 新增 Instinct 召回章节，按 domain 和 trigger 匹配
- `GATE-2` 新增第 4 项校验：Instinct 召回，confidence 分流（>=0.7 自动应用 / <0.7 仅提示）
- `REF_SYNTAX` 新增 `[L4:instinct:name]` 引用语法
- 3 条示例 instinct 覆盖预算偏差/勾稽校验/现金流分类场景
- instinct-template.yml 模板

### 变更

- Instinct 生命周期管理：自动生成、手动创建、更新、失效（confidence < 0.3 静默停用）

## v4.0.0 - 2026-07-31

### 新增

- 三层分离架构：引擎层 `core/` + 配置层 `packs/` + 数据层 `data-buffer/`
- 四层经验包结构：L1 规则 + L2 模板 + L3 案例 + L4 决策记录
- 两级 Gate 机制（Gate-1 数据准入 + Gate-2 产出校验），均为非阻断式
- 引用语法：`[L1:name]` `[L2:name]` `[L3:name]` `[L4:name]`
- 纯约定扫描（去除 pack.yml），元数据从文件内容推断
- 三原则：数据责任归用户、用户自主可控、核心框架稳定
- 3 个 Python 工具：init_pack.py / validate_pack.py / scan_pack.py
- water-soe-finance 经验包：33 条规则、7 个模板、15 个案例
- _template 空白经验包模板
- 平台适配器（千帆 + 通用）
- MIT 许可证
