#!/usr/bin/env python3
"""
WordPress 连接测试脚本（支持 REST API 和 XML-RPC）
用于诊断 WordPress 连接问题
"""

import sys
import requests
import yaml
import base64
from pathlib import Path


def test_rest_api_availability(base_url):
    """测试 WordPress REST API 是否可用"""
    print(f"\n1. 测试 REST API 端点是否可访问...")
    api_url = f"{base_url}/wp-json/wp/v2"
    print(f"   URL: {api_url}")

    try:
        response = requests.get(f"{base_url}/wp-json", timeout=10)

        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("   ✓ REST API 端点可访问")
            print(f"   站点名称: {data.get('name', 'Unknown')}")
            print(f"   API 命名空间: {data.get('namespaces', [])}")
            return True
        else:
            print(f"   ❌ REST API 不可访问 (状态码: {response.status_code})")
            return False

    except requests.exceptions.Timeout:
        print("   ❌ 连接超时")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ 连接错误: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False


def test_rest_api_authentication(base_url, username, password):
    """测试 REST API 认证"""
    print(f"\n2. 测试 REST API 认证...")

    try:
        api_url = f"{base_url}/wp-json/wp/v2"

        # 创建认证头
        credentials = f"{username}:{password}"
        token = base64.b64encode(credentials.encode()).decode()
        headers = {
            'Authorization': f'Basic {token}',
            'Content-Type': 'application/json'
        }

        # 尝试获取当前用户信息
        response = requests.get(
            f"{api_url}/users/me",
            headers=headers,
            timeout=10
        )

        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            user_data = response.json()
            print("   ✓ REST API 认证成功")
            print(f"   用户ID: {user_data.get('id')}")
            print(f"   用户名: {user_data.get('name')}")
            print(f"   角色: {user_data.get('roles', [])}")
            return True
        elif response.status_code == 401:
            print("   ❌ 认证失败：用户名或密码错误")
            print("\n   解决方法：")
            print("   1. 检查用户名和密码是否正确")
            print("   2. 使用应用密码（推荐）：")
            print("      - 登录 WordPress 后台")
            print("      - 用户 > 个人资料 > 应用密码")
            print("      - 创建新的应用密码")
            return False
        elif response.status_code == 403:
            print("   ❌ 权限不足")
            print("   请确保该用户有发布文章的权限")
            return False
        else:
            print(f"   ❌ 意外的状态码: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False


def test_rest_api_post_creation(base_url, username, password):
    """测试 REST API 创建文章"""
    print(f"\n3. 测试 REST API 创建草稿...")

    try:
        api_url = f"{base_url}/wp-json/wp/v2"

        credentials = f"{username}:{password}"
        token = base64.b64encode(credentials.encode()).decode()
        headers = {
            'Authorization': f'Basic {token}',
            'Content-Type': 'application/json'
        }

        # 创建测试文章
        post_data = {
            'title': '[测试] AutoPost 连接测试',
            'content': '<p>这是一篇由 AutoPost 工具创建的测试文章。如果您看到这篇文章，说明连接成功。</p><p>您可以安全地删除此文章。</p>',
            'status': 'draft'
        }

        response = requests.post(
            f"{api_url}/posts",
            headers=headers,
            json=post_data,
            timeout=30
        )

        print(f"   状态码: {response.status_code}")

        if response.status_code == 201:
            post = response.json()
            print("   ✓ 成功创建测试文章（草稿）")
            print(f"   文章ID: {post.get('id')}")
            print(f"   标题: {post.get('title', {}).get('rendered')}")
            print(f"   预览链接: {post.get('link')}")
            print("\n   注意：这是一篇测试文章，您可以在 WordPress 后台删除它")
            return True
        else:
            print(f"   ❌ 创建文章失败")
            print(f"   响应: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False


def test_xmlrpc_availability(url):
    """测试 XML-RPC 是否可用"""
    print(f"\n4. 测试 XML-RPC 端点是否可访问...")
    print(f"   URL: {url}")

    try:
        response = requests.post(
            url,
            data='<?xml version="1.0"?><methodCall><methodName>demo.sayHello</methodName></methodCall>',
            headers={'Content-Type': 'text/xml'},
            timeout=10
        )

        print(f"   状态码: {response.status_code}")

        if response.status_code == 200:
            print("   ✓ XML-RPC 端点可访问")
            return True
        elif response.status_code == 403:
            print("   ❌ 403 Forbidden - XML-RPC 被阻止")
            print("   可能原因：")
            print("   - XML-RPC 功能被禁用")
            print("   - 安全插件（如 Wordfence、iThemes Security）阻止了 XML-RPC")
            print("   - 服务器防火墙规则")
            return False
        elif response.status_code == 405:
            print("   ✓ XML-RPC 端点存在（405 Method Not Allowed 是正常的）")
            return True
        else:
            print(f"   ⚠️  意外的状态码: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print("   ❌ 连接超时")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ 连接错误: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False


def test_xmlrpc_connection(url, username, password):
    """测试 XML-RPC 连接"""
    print(f"\n5. 测试 XML-RPC 认证...")

    try:
        from wordpress_xmlrpc import Client
        from wordpress_xmlrpc.methods import posts

        client = Client(url, username, password)

        # 尝试获取最近的文章
        posts_list = client.call(posts.GetPosts({'number': 1}))

        print("   ✓ XML-RPC 认证成功")
        print(f"   已连接到站点，可以访问文章")
        return True

    except ImportError:
        print("   ⚠️  未安装 python-wordpress-xmlrpc 库")
        print("   如需使用 XML-RPC，请运行：pip install python-wordpress-xmlrpc")
        return False
    except Exception as e:
        error_str = str(e)
        print(f"   ❌ XML-RPC 认证失败: {error_str}")

        if "403" in error_str or "Forbidden" in error_str:
            print("\n   403 错误的常见解决方法：")
            print("   1. 检查 WordPress 后台设置")
            print("      - 登录 WordPress 后台")
            print("      - 进入 设置 > 撰写")
            print("      - 确保没有禁用 XML-RPC")
            print()
            print("   2. 检查安全插件")
            print("      - Wordfence: Security > All Options > 搜索 'XML-RPC'")
            print("      - iThemes Security: 检查 'WordPress Tweaks' 设置")
            print()
            print("   3. 建议使用 REST API（更现代、更安全）")

        return False


def main():
    print("=" * 70)
    print("WordPress 连接测试工具（支持 REST API 和 XML-RPC）")
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

    url = wp_config.get('url')
    username = wp_config.get('username')
    password = wp_config.get('password')

    # 处理 URL
    if url.endswith('/xmlrpc.php'):
        base_url = url[:-12]
        xmlrpc_url = url
    else:
        base_url = url.rstrip('/')
        xmlrpc_url = f"{base_url}/xmlrpc.php"

    # 确保有协议前缀
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
        xmlrpc_url = 'https://' + xmlrpc_url

    print(f"\n配置信息:")
    print(f"  站点URL: {base_url}")
    print(f"  用户名: {username}")
    print(f"  密码: {'*' * len(password)}")
    print(f"  API方式: {wp_config.get('api_method', 'auto')}")

    rest_ok = False
    xmlrpc_ok = False

    # 测试 REST API
    print("\n" + "=" * 70)
    print("测试 REST API")
    print("=" * 70)

    if test_rest_api_availability(base_url):
        if test_rest_api_authentication(base_url, username, password):
            if test_rest_api_post_creation(base_url, username, password):
                rest_ok = True

    # 测试 XML-RPC
    print("\n" + "=" * 70)
    print("测试 XML-RPC")
    print("=" * 70)

    if test_xmlrpc_availability(xmlrpc_url):
        if test_xmlrpc_connection(xmlrpc_url, username, password):
            xmlrpc_ok = True

    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)

    if rest_ok:
        print("✓ REST API: 可用（推荐）")
        print("  建议在 config.yaml 中设置: api_method: 'rest'")
    else:
        print("❌ REST API: 不可用")

    if xmlrpc_ok:
        print("✓ XML-RPC: 可用")
        print("  可以在 config.yaml 中设置: api_method: 'xmlrpc'")
    else:
        print("❌ XML-RPC: 不可用")

    if not rest_ok and not xmlrpc_ok:
        print("\n⚠️  两种 API 方式都不可用")
        print("\n推荐步骤：")
        print("1. 创建应用密码（WordPress 5.6+）：")
        print("   - 登录 WordPress 后台")
        print("   - 用户 > 个人资料 > 应用密码")
        print("   - 创建新的应用密码并更新 config.yaml")
        print()
        print("2. 如果使用了安全插件，请检查相关设置")
        print("3. REST API 通常更稳定，建议优先使用")
        return 1
    elif rest_ok:
        print("\n✓ 推荐使用 REST API 进行发布")
        return 0
    else:
        print("\n✓ 可以使用 XML-RPC 进行发布")
        return 0


if __name__ == "__main__":
    sys.exit(main())
