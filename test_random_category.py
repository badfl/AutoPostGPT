#!/usr/bin/env python3
"""
测试随机分类功能
"""

import yaml
from pathlib import Path
from publisher import create_publisher


def main():
    print("=" * 70)
    print("WordPress 随机分类测试")
    print("=" * 70)

    # 加载配置
    config_file = Path("config.yaml")
    if not config_file.exists():
        print("\n❌ 未找到 config.yaml 文件")
        return 1

    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    wp_config = config.get('wordpress', {})

    if not wp_config.get('enabled', False):
        print("\n⚠️  WordPress 功能未启用")
        return 0

    # 创建发布器
    print("\n正在连接 WordPress...")
    publisher = create_publisher(wp_config)

    if not publisher:
        print("❌ 无法创建发布器")
        return 1

    if not publisher.test_connection():
        print("❌ 连接失败")
        return 1

    print("✓ 连接成功\n")

    # 获取所有分类
    print("获取所有分类...")
    if hasattr(publisher, 'get_all_categories'):
        categories = publisher.get_all_categories()

        if categories:
            print(f"\n找到 {len(categories)} 个分类：")
            for cat in categories:
                if hasattr(cat, 'name'):  # XML-RPC
                    print(f"  - {cat.name} (ID: {cat.id})")
                else:  # REST API
                    print(f"  - {cat['name']} (ID: {cat['id']})")
        else:
            print("❌ 未找到任何分类")
            return 1

        # 测试随机选择分类
        print("\n测试随机选择分类 (3次)：")
        for i in range(3):
            if hasattr(publisher, 'get_random_category_id'):
                # REST API
                random_id = publisher.get_random_category_id()
                print(f"  第 {i+1} 次随机选择 - ID: {random_id}")
            else:
                # XML-RPC
                random_cat = publisher.get_random_category()
                if random_cat:
                    print(f"  第 {i+1} 次随机选择 - {random_cat[0]} (ID: {random_cat[1]})")

        print("\n✓ 随机分类功能正常")
    else:
        print("❌ 发布器不支持获取分类列表")
        return 1

    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    exit(main())
