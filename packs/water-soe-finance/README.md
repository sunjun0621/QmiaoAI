# 水务国企财务经验包

> 版本：4.3.0 | 领域：水务公用事业 / 国企财务 | 适用引擎：>=4.0.0

## 概述

面向水务公用事业国企的财务分析经验包，覆盖会计核算、异常检测、审计合规、预算执行四大场景。

## L1 规则（33 条）

### core 规则（10 条，始终加载）

| 文件 | 规则数 | 覆盖范围 |
|------|--------|----------|
| `accounting.yml` | 8 条 | 收入-成本-费用=利润、资产负债恒等式、现金流量勾稽、折旧计提、收入确认、成本匹配、资产减值、借款费用资本化 |
| `checklist.yml` | 2 条 | 数据脱敏检查、格式规范检查 |

### context 规则（23 条，关键词触发）

| 文件 | 规则数 | keywords | 覆盖范围 |
|------|--------|----------|----------|
| `anomaly.yml` | 10 条 | 偏差、异常、波动、产销差、水费 | 产销差率、水费回收率、单位成本、人均费用、漏损率、维修费占比、能耗成本比、应收账款周转、资本性支出占比、资产负债率 |
| `audit.yml` | 11 条 | 审计、合规、披露、内部控制、政府补助 | 政府补助披露、关联交易披露、或有事项披露、固定资产盘点、在建工程转固、无形资产摊销、长期股权投资、借款费用资本化、收入确认时点、坏账准备计提、存货盘点 |
| `variance.yml` | 2 条 | 预算、执行、偏差、决算 | 水费收入预算执行、管网维护费预算执行 |

## L2 模板（7 个）

| 模板 | 用途 | 引用的 L1 规则 |
|------|------|---------------|
| `monthly-analysis.md` | 月度财务分析 | core:accounting, core:checklist, context:anomaly, context:variance |
| `monthly-report.md` | 经济效益月报（财资〔2025〕161号格式） | core:accounting, context:anomaly |
| `special-analysis.md` | 专项分析（产销差、成本等） | core:accounting, context:anomaly |
| `annual-report.md` | 年度财务分析报告 | core:accounting, core:checklist, context:anomaly, context:audit, context:variance |
| `balance-sheet.md` | 资产负债表 | core:accounting |
| `income-statement.md` | 利润表 | core:accounting |
| `cash-flow-statement.md` | 现金流量表 | core:accounting |

## L3 案例（15 个）

| 案例 | 场景 | 关联规则 |
|------|------|----------|
| case-001 | 产销差异常偏高 | anm-nrw-variance |
| case-002 | 水费收入缺口分析 | var-water-revenue-budget |
| case-003 | 运营成本超支 | anm-unit-cost |
| case-004 | 应收账款风险 | anm-receivable-turnover |
| case-005 | 政府补助确认 | aud-subsidy-disclosure |
| case-006 | 折旧政策变更 | acc-depreciation |
| case-007 | 资产减值准备 | acc-impairment |
| case-008 | 借款费用资本化 | acc-loan-capitalization, aud-loan-capitalization |
| case-009 | 或有事项披露 | aud-contingency-disclosure |
| case-010 | 关联交易披露 | aud-related-party |
| case-011 | 资本性支出预算偏差 | var-pipeline-budget, anm-capex-ratio |
| case-012 | 水费收入与供水量匹配 | anm-revenue-collection |
| case-013 | 政府补助完整性检查 | aud-subsidy-disclosure |
| case-014 | 折旧率异常 | acc-depreciation |
| case-015 | 借款利息异常 | acc-loan-capitalization |

## L4 决策记录

| 文件 | 说明 |
|------|------|
| `2026-07-monthly-analysis.md` | 2026年7月月度分析决策记录 |
| `2026-08-02-evidence-chain-example.md` | 证据链示例 |
| `decision-template.md` | 决策记录模板 |

## L4 Instinct（4 个）

| 文件 | trigger | confidence |
|------|---------|------------|
| `budget-variance-pipeline.yml` | 预算执行偏差分析 | 0.7 |
| `cashflow-operating-classification.yml` | 经营活动现金流分类 | 0.8 |
| `reconciliation-depreciation-first.yml` | 勾稽校验折旧优先 | 0.8 |
| `instinct-template.yml` | 模板（参考用） | - |

## 使用方式

1. 加载引擎（`core/SYSTEM-FULL.md`）
2. 将本经验包文件提供给 AI（知识库或对话）
3. 提供脱敏数据
4. 发出指令，如"分析本月产销差"

## 验证

```bash
python tools/validate_pack.py packs/water-soe-finance/
python tools/scan_pack.py packs/water-soe-finance/
```
