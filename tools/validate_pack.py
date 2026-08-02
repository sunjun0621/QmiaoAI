#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
经验包校验工具 v4.0
用法: python validate_pack.py packs/your-pack/

v4.0 变更:
- 无 pack.yml，改为纯约定扫描校验
- 校验 L1-rules/ L2-templates/ L3-cases/ L4-decision-logs/ 四层目录
- L4-decision-logs/ 可为空（首次使用）
"""

import sys
import os
import re


def validate_pack(pack_dir):
    """校验经验包（v4.0 L1-L4 结构）"""
    errors = []
    warnings = []
    info = []

    pack_id = os.path.basename(os.path.normpath(pack_dir))
    info.append(f"经验包 ID: {pack_id}")

    # 1. 检查 L1-rules/ 目录
    l1_dir = os.path.join(pack_dir, "L1-rules")
    if os.path.isdir(l1_dir):
        rule_files = [f for f in os.listdir(l1_dir) if f.endswith(".yml")]
        if not rule_files:
            warnings.append("L1-rules/ 目录为空")
        for rf in rule_files:
            rf_path = os.path.join(l1_dir, rf)
            with open(rf_path, "r", encoding="utf-8") as f:
                rule_content = f.read()
            if "checks:" not in rule_content:
                warnings.append(f"L1-rules/{rf} 中未找到 'checks:' 键")
            rule_blocks = re.findall(
                r"(- id:.*?)(?=\n\s*- id:|\Z)", rule_content, re.DOTALL
            )
            for block in rule_blocks:
                for field in ["id:", "name:", "rule:", "severity:", "message:"]:
                    if field not in block:
                        errors.append(f"L1-rules/{rf} 中有规则缺少字段: {field}")
                sev_match = re.search(r"severity:\s*(\w+)", block)
                if sev_match and sev_match.group(1) not in ["info", "warn", "alert"]:
                    errors.append(
                        f"L1-rules/{rf} 中有规则 severity 值不合法: {sev_match.group(1)}"
                    )
        info.append(f"L1 规则文件数: {len(rule_files)}")
    else:
        errors.append("缺少 L1-rules/ 目录（经验包至少需要 L1 或 L2 之一）")

    # 2. 检查 L2-templates/ 目录
    l2_dir = os.path.join(pack_dir, "L2-templates")
    if os.path.isdir(l2_dir):
        tpl_files = [f for f in os.listdir(l2_dir) if f.endswith(".md")]
        if not tpl_files:
            warnings.append("L2-templates/ 目录为空")
        else:
            for tf in tpl_files:
                tf_path = os.path.join(l2_dir, tf)
                with open(tf_path, "r", encoding="utf-8") as f:
                    tpl_content = f.read()
                # 检查模板是否包含引用语法声明
                ref_pattern = re.findall(r"\[L1:\w[\w-]*\]", tpl_content)
                if ref_pattern:
                    info.append(
                        f"L2-templates/{tf} 引用了 {len(set(ref_pattern))} 个 L1 规则"
                    )
        info.append(f"L2 模板文件数: {len(tpl_files)}")
    else:
        errors.append("缺少 L2-templates/ 目录（经验包至少需要 L1 或 L2 之一）")

    # 3. 检查 L3-cases/ 目录
    l3_dir = os.path.join(pack_dir, "L3-cases")
    if os.path.isdir(l3_dir):
        case_files = [f for f in os.listdir(l3_dir) if f.endswith(".md")]
        info.append(f"L3 案例数量: {len(case_files)}")
        sensitive_patterns = [
            r"\d{16,19}",
            r"\d{15,18}",
            r"1[3-9]\d{9}",
        ]
        for cf in case_files:
            cf_path = os.path.join(l3_dir, cf)
            with open(cf_path, "r", encoding="utf-8") as f:
                case_content = f.read()
            for pattern in sensitive_patterns:
                matches = re.findall(pattern, case_content)
                if matches:
                    warnings.append(
                        f"L3-cases/{cf} 中可能包含未脱敏的敏感数字: {matches[:3]}"
                    )
    else:
        info.append("无 L3-cases/ 目录（可选）")

    # 4. 检查 L4-decision-logs/ 目录
    l4_dir = os.path.join(pack_dir, "L4-decision-logs")
    if os.path.isdir(l4_dir):
        log_files = [f for f in os.listdir(l4_dir) if f.endswith(".md")]
        info.append(f"L4 决策记录数: {len(log_files)}（首次使用为空属正常）")
    else:
        warnings.append("缺少 L4-decision-logs/ 目录（建议创建，AI 会自动写入）")

    # 5. 检查 README.md
    readme_path = os.path.join(pack_dir, "README.md")
    if not os.path.exists(readme_path):
        warnings.append("缺少 README.md（用于元数据推断）")
    else:
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_content = f.read()
        if "版本" not in readme_content and "version" not in readme_content.lower():
            warnings.append("README.md 中未标注版本号（建议标注以便元数据推断）")

    # 6. 统计信息
    info.append(f"经验包目录: {pack_dir}")

    return errors, warnings, info


def main():
    if len(sys.argv) < 2:
        print("用法: python validate_pack.py <pack_dir>")
        print("示例: python validate_pack.py packs/water-soe-finance/")
        sys.exit(1)

    pack_dir = sys.argv[1]
    if not os.path.isdir(pack_dir):
        print(f"错误: 目录不存在: {pack_dir}")
        sys.exit(1)

    errors, warnings, info = validate_pack(pack_dir)

    print("=" * 50)
    print("经验包校验报告 (v4.0)")
    print("=" * 50)

    for i in info:
        print(f"  [INFO] {i}")

    for w in warnings:
        print(f"  [WARN] {w}")

    for e in errors:
        print(f"  [ERROR] {e}")

    print("-" * 50)
    if errors:
        print(f"校验结果: 未通过 ({len(errors)} 错误, {len(warnings)} 警告)")
        sys.exit(1)
    elif warnings:
        print(f"校验结果: 通过但有警告 ({len(warnings)} 警告)")
    else:
        print("校验结果: 全部通过")
    sys.exit(0)


if __name__ == "__main__":
    main()
