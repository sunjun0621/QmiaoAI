# 技能扩展

> 钱喵 AI 财务助手的技能扩展机制。

## 什么是技能

技能是引擎层之上的扩展能力，用 Python 脚本实现，提供引擎指令无法覆盖的自动化操作。

## 内置工具脚本

位于 `tools/` 目录：

| 脚本 | 功能 | 使用场景 |
|------|------|----------|
| `init_pack.py` | 从模板创建新经验包 | 初始化新行业经验包 |
| `validate_pack.py` | 校验经验包结构和内容 | 开发完成后校验 |
| `scan_pack.py` | 安全扫描（prompt injection 检测） | 上传前安全检查 |

## 使用方式

```bash
# 创建新经验包
python tools/init_pack.py manufacturing "制造业财务经验包"

# 校验经验包
python tools/validate_pack.py packs/water-soe-finance/

# 安全扫描
python tools/scan_pack.py --all
```

## 扩展方向

- 格式转换（CSV/Excel/PDF 互转）
- 对话转案例（自动整理为 L3 案例格式）
- 财经新闻每日看
- 批量处理（多月份批量分析）
