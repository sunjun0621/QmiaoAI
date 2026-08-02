# 贡献指南

感谢你对钱喵 AI 财务助手的关注。以下是如何参与项目贡献的说明。

## 贡献方式

### 报告问题

在 GitHub Issues 中提交问题，请包含：

- 问题的具体描述和复现步骤
- 使用的版本号（查看 `core/VERSION.json`）
- 经验包名称（如 water-soe-finance）
- 预期行为与实际行为的差异

### 改进经验包

经验包是最常见的贡献方向：

- 补充 L1 规则（新增阈值、审计检查项）
- 完善 L2 模板（新增报告类型、优化产出格式）
- 贡献 L3 案例（脱敏后的真实处理经验）
- 调整 L4 instinct（优化 confidence 和 action）

### 改进引擎

引擎层（`core/`）变更需要谨慎，因为影响所有经验包：

- 修复逻辑错误
- 优化输出格式
- 新增引擎能力（需同步更新 SYSTEM.md 和相关模块）

### 开发工具

`tools/` 目录下的 Python 脚本可以增强项目管理能力：

- 新增校验规则
- 优化安全扫描模式
- 开发批量处理工具

## 开发流程

1. Fork 仓库
2. 创建分支：`git checkout -b feature/your-feature`
3. 修改并测试
4. 运行校验：`python tools/validate_pack.py packs/your-pack/`
5. 运行安全扫描：`python tools/scan_pack.py --all`
6. 提交：`git commit -m "描述你的变更"`
7. 推送并发起 Pull Request

## 经验包开发规范

### L1 规则文件格式

```yaml
# 文件头注释（说明用途和引用语法）

keywords: [关键词1, 关键词2]  # 仅 context 文件需要

checks:
  - id: 规则唯一标识
    name: 规则名称
    rule: "规则表达式"
    severity: warn  # alert / warn / info
    message: "提示消息"
    variables:
      变量名: "变量说明"
```

### L2 模板文件格式

```markdown
---
rules: [L1:core:accounting], [L1:context:anomaly]
---

# 任务模板：模板名称

## 任务说明
...

## 执行步骤
...

## 产出格式
...
```

### L3 案例文件格式

```markdown
# 案例：案例名称

## 背景
## 问题
## 处理方法
## 结果
## 经验总结
## 标签

> 案例中的数据已脱敏，不包含真实业务数据。
```

### 命名约定

- 经验包 ID：小写英文 + 连字符（如 `water-soe-finance`）
- 规则 ID：`前缀-简述`（如 `anm-nrw-variance`、`aud-wsoe-reconciliation`）
- 案例文件：`case-NNN-简述.md`（如 `case-001-water-loss.md`）
- 决策记录：`YYYY-MM-DD-简述.md`（如 `2026-07-monthly-analysis.md`）
- Instinct：`简述.yml`（如 `budget-variance-pipeline.yml`）

## 代码风格

- Markdown：使用 `##` 作为章节标题，`###` 作为子章节
- YAML：2 空格缩进，字符串值用双引号
- Python：遵循 PEP 8，文件头注明用途和用法

## 安全要求

- 不得在经验包中包含真实业务数据
- L3 案例必须脱敏（`validate_pack.py` 会检测疑似敏感数字）
- 不得在规则文件中包含 API Key、密码等凭据
- 外部 URL 仅限政府部门和财税机构官网（`scan_pack.py` 白名单）

## 版本兼容

- 引擎变更需保持向后兼容
- 新增语法不破坏旧格式解析
- 经验包最低兼容版本：`>=1.0.0`
