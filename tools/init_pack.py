#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
经验包初始化工具 v1.0
用法: python init_pack.py <pack-id> <pack-name>
示例: python init_pack.py manufacturing "制造业财务经验包"

v1.0 变更: 无 pack.yml，纯约定扫描。从 _template 复制 L1-L4 四层目录结构。
"""

import sys
import os
import shutil
import re


def init_pack(pack_id, pack_name):
    """从 _template 创建新经验包（L1-L4 四层结构）"""
    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "packs", "_template"
    )
    pack_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "packs", pack_id
    )

    # 检查 id 格式
    if not re.match(r"^[a-z0-9-]+$", pack_id):
        print(f"错误: pack-id 格式不正确，应为小写英文+连字符: {pack_id}")
        sys.exit(1)

    # 检查目录是否已存在
    if os.path.exists(pack_dir):
        print(f"错误: 经验包已存在: {pack_dir}")
        sys.exit(1)

    # 检查模板目录
    if not os.path.exists(template_dir):
        print(f"错误: 模板目录不存在: {template_dir}")
        sys.exit(1)

    # 复制模板
    shutil.copytree(template_dir, pack_dir)
    print(f"已创建经验包目录: {pack_dir}")

    # 修改 README.md（替代 pack.yml 的元数据声明作用）
    readme_path = os.path.join(pack_dir, "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("空白经验包模板", pack_name)
    content = content.replace("your-domain", pack_id)
    content = content.replace("1.0.0", "1.0.0")
    content = content.replace(
        "这是一个空白经验包模板，用于快速创建你自己的领域经验包。复制此目录到 `packs/{your-pack-id}/`，然后填写各层内容。",
        f"{pack_name} - 请补充适用场景描述",
    )

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"已生成 README.md")

    # 创建 L4 .gitkeep
    l4_dir = os.path.join(pack_dir, "L4-decision-logs")
    gitkeep_path = os.path.join(l4_dir, ".gitkeep")
    if not os.path.exists(gitkeep_path):
        with open(gitkeep_path, "w", encoding="utf-8") as f:
            f.write("")

    print()
    print("=" * 50)
    print("经验包已创建（v1.0 纯约定扫描，无 pack.yml）")
    print("下一步操作：")
    print(f"  1. 编辑 packs/{pack_id}/README.md 填写经验包说明")
    print(f"  2. 编辑 packs/{pack_id}/L1-rules/ 下的规则文件")
    print(f"  3. 编辑 packs/{pack_id}/L2-templates/ 下的模板文件")
    print(f"  4. 在 packs/{pack_id}/L3-cases/ 添加脱敏案例")
    print(f"  5. L4-decision-logs/ 由 AI 自动写入，无需手动操作")
    print(f"  6. 运行校验: python tools/validate_pack.py packs/{pack_id}/")
    print("=" * 50)


def main():
    if len(sys.argv) < 3:
        print("用法: python init_pack.py <pack-id> <pack-name>")
        print('示例: python init_pack.py manufacturing "制造业财务经验包"')
        sys.exit(1)

    pack_id = sys.argv[1]
    pack_name = sys.argv[2]
    init_pack(pack_id, pack_name)


if __name__ == "__main__":
    main()
