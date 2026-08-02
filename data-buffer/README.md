# 数据缓冲区

> 用户数据的入口和 AI 产出的出口。全部 `.gitignore`，不进入版本控制。

## 目录结构

```
data-buffer/
├── input/           # 用户输入的脱敏数据
│   ├── .gitkeep
│   └── test-water-202607.md   # 测试数据（可删除）
├── output/          # AI 生成的产出文件
│   ├── .gitkeep
│   ├── instinct-recall-verification-20260802.md  # 验证产出（可删除）
│   └── reviewer-validation-20260802.md            # 验证产出（可删除）
└── templates/       # 数据模板（可提交）
    ├── monthly-data.csv       # 月度财务数据模板
    ├── budget-data.csv        # 预算数据模板
    └── reconciliation.csv     # 勾稽数据模板
```

## 使用方式

### 输入数据

1. 从 `templates/` 复制合适的模板到 `input/`
2. 填入脱敏数据
3. 在对话中引用该文件，或直接在对话中粘贴数据

也可以不使用模板，直接在对话中提供 CSV 或文本格式的数据。

### 输出文件

AI 生成的报告和分析结果会写入 `output/` 目录。这些文件可以随时删除。

## 数据模板

### monthly-data.csv

月度财务数据模板，包含科目、本期金额、上期金额、预算金额、同比变动、预算执行率。

### budget-data.csv

预算数据模板，按季度拆分年度预算，含累计执行列。

### reconciliation.csv

勾稽数据模板，包含收入、成本、费用、利润及资产负债表和现金流量表关键科目。

## 数据安全

- **脱敏由用户全权负责**：确保删除或替换所有银行账号、身份证号、手机号等敏感信息
- **Gate-1 提示但不强制**：Gate-1 会一次性提示确认脱敏，但不会阻断处理
- **不进入版本控制**：`input/` 和 `output/` 目录全部 `.gitignore`，仅 `.gitkeep` 和 `templates/` 被跟踪
