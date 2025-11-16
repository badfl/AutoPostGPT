#!/usr/bin/env python3
"""
Publisher - WordPress 发布模块（支持 XML-RPC 和 REST API）
负责将文章发布到 WordPress
"""

import logging
import requests
import base64
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class WordPressPublisherBase(ABC):
    """WordPress 发布器基类"""

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        default_category: str = "未分类",
        default_status: str = "draft"
    ):
        self.logger = logging.getLogger(__name__)
        self.url = url
        self.username = username
        self.password = password
        self.default_category = default_category
        self.default_status = default_status

    @abstractmethod
    def test_connection(self) -> bool:
        """测试连接"""
        pass

    @abstractmethod
    def publish_post(
        self,
        title: str,
        content: str,
        category: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[list] = None,
        excerpt: Optional[str] = None
    ) -> Optional[str]:
        """发布文章"""
        pass


class WordPressRESTPublisher(WordPressPublisherBase):
    """WordPress REST API 发布器"""

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        default_category: str = "未分类",
        default_status: str = "draft"
    ):
        """
        初始化 WordPress REST API 发布器

        Args:
            url: WordPress 站点 URL (如 https://yourblog.com)
            username: WordPress 用户名
            password: WordPress 应用密码或账户密码
            default_category: 默认分类
            default_status: 默认状态 (draft 或 publish)
        """
        super().__init__(url, username, password, default_category, default_status)

        # 移除 /xmlrpc.php 后缀（如果有）
        if url.endswith('/xmlrpc.php'):
            url = url[:-12]

        # 确保 URL 包含协议
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # 移除末尾的斜杠
        self.base_url = url.rstrip('/')
        self.api_url = f"{self.base_url}/wp-json/wp/v2"

        # 设置认证头
        credentials = f"{username}:{password}"
        token = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {token}',
            'Content-Type': 'application/json'
        }

        self.logger.info(f"WordPress REST API 客户端初始化: {self.base_url}")

    def test_connection(self) -> bool:
        """测试 WordPress REST API 连接"""
        try:
            # 测试获取当前用户信息
            response = requests.get(
                f"{self.api_url}/users/me",
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                user_data = response.json()
                self.logger.info(f"REST API 连接成功，用户: {user_data.get('name', 'Unknown')}")
                return True
            elif response.status_code == 401:
                self.logger.error("REST API 认证失败：用户名或密码错误")
                return False
            else:
                self.logger.error(f"REST API 连接失败：状态码 {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            self.logger.error(f"REST API 连接测试失败: {e}")
            return False

    def get_all_categories(self) -> list:
        """获取所有分类"""
        try:
            response = requests.get(
                f"{self.api_url}/categories",
                headers=self.headers,
                params={'per_page': 100},  # 获取最多100个分类
                timeout=10
            )

            if response.status_code == 200:
                categories = response.json()
                self.logger.info(f"获取到 {len(categories)} 个分类")
                return categories
            else:
                self.logger.error(f"获取分类列表失败: {response.status_code}")
                return []

        except Exception as e:
            self.logger.error(f"获取分类列表失败: {e}")
            return []

    def get_random_category_id(self) -> Optional[int]:
        """随机选择一个分类 ID"""
        try:
            import random
            categories = self.get_all_categories()

            if not categories:
                self.logger.warning("没有可用的分类")
                return None

            # 过滤掉"未分类"（Uncategorized），通常 ID 为 1
            valid_categories = [cat for cat in categories if cat['id'] != 1]

            if not valid_categories:
                # 如果只有"未分类"，就使用它
                valid_categories = categories

            random_cat = random.choice(valid_categories)
            self.logger.info(f"随机选择分类: {random_cat['name']} (ID: {random_cat['id']})")
            return random_cat['id']

        except Exception as e:
            self.logger.error(f"随机选择分类失败: {e}")
            return None

    def get_category_id(self, category_name: str) -> Optional[int]:
        """获取分类 ID"""
        try:
            response = requests.get(
                f"{self.api_url}/categories",
                headers=self.headers,
                params={'search': category_name},
                timeout=10
            )

            if response.status_code == 200:
                categories = response.json()
                for cat in categories:
                    if cat['name'] == category_name:
                        self.logger.info(f"找到分类: {category_name} (ID: {cat['id']})")
                        return cat['id']

            self.logger.warning(f"未找到分类: {category_name}")
            return None

        except Exception as e:
            self.logger.error(f"获取分类 ID 失败: {e}")
            return None

    def create_tag(self, tag_name: str) -> Optional[int]:
        """创建标签并返回 ID"""
        try:
            response = requests.post(
                f"{self.api_url}/tags",
                headers=self.headers,
                json={'name': tag_name},
                timeout=10
            )

            if response.status_code == 201:
                tag_data = response.json()
                return tag_data['id']
            elif response.status_code == 400:
                # 标签可能已存在，尝试获取
                response = requests.get(
                    f"{self.api_url}/tags",
                    headers=self.headers,
                    params={'search': tag_name},
                    timeout=10
                )
                if response.status_code == 200:
                    tags = response.json()
                    for tag in tags:
                        if tag['name'] == tag_name:
                            return tag['id']

            return None

        except Exception as e:
            self.logger.error(f"创建标签失败: {e}")
            return None

    def publish_post(
        self,
        title: str,
        content: str,
        category: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[list] = None,
        excerpt: Optional[str] = None
    ) -> Optional[str]:
        """发布文章到 WordPress（REST API）"""
        try:
            self.logger.info(f"准备发布文章 (REST API): {title}")

            # 构建文章数据
            post_data = {
                'title': title,
                'content': content,
                'status': status or self.default_status
            }

            # 设置摘要
            if excerpt:
                post_data['excerpt'] = excerpt

            # 设置分类
            category_name = category or self.default_category
            category_id = None

            if category_name:
                # 如果指定了分类名称，尝试查找
                category_id = self.get_category_id(category_name)

            if not category_id:
                # 如果没有指定分类或未找到指定分类，随机选择一个
                self.logger.info("未指定分类或未找到指定分类，将随机选择分类")
                category_id = self.get_random_category_id()

            if category_id:
                post_data['categories'] = [category_id]

            # 设置标签
            if tags:
                tag_ids = []
                for tag_name in tags:
                    tag_id = self.create_tag(tag_name)
                    if tag_id:
                        tag_ids.append(tag_id)
                if tag_ids:
                    post_data['tags'] = tag_ids

            # 发布文章
            response = requests.post(
                f"{self.api_url}/posts",
                headers=self.headers,
                json=post_data,
                timeout=30
            )

            if response.status_code == 201:
                post = response.json()
                post_id = str(post['id'])
                status_text = "已发布" if post_data['status'] == "publish" else "已保存为草稿"
                self.logger.info(f"文章 {status_text}: {title} (ID: {post_id})")
                self.logger.info(f"预览链接: {post.get('link', 'N/A')}")
                return post_id
            else:
                self.logger.error(f"发布文章失败：{response.status_code} - {response.text}")
                return None

        except Exception as e:
            self.logger.error(f"发布文章失败 (REST API): {e}")
            return None


class WordPressXMLRPCPublisher(WordPressPublisherBase):
    """WordPress XML-RPC 发布器"""

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        default_category: str = "未分类",
        default_status: str = "draft"
    ):
        """
        初始化 WordPress XML-RPC 发布器

        Args:
            url: WordPress XML-RPC URL (如 https://yourblog.com/xmlrpc.php)
            username: WordPress 用户名
            password: WordPress 密码
            default_category: 默认分类
            default_status: 默认状态 (draft 或 publish)
        """
        super().__init__(url, username, password, default_category, default_status)

        try:
            from wordpress_xmlrpc import Client, WordPressPost
            from wordpress_xmlrpc.methods.posts import NewPost
            from wordpress_xmlrpc.methods.taxonomies import GetTerms

            self.Client = Client
            self.WordPressPost = WordPressPost
            self.NewPost = NewPost
            self.GetTerms = GetTerms

        except ImportError:
            raise ImportError("需要安装 python-wordpress-xmlrpc: pip install python-wordpress-xmlrpc")

        # 确保 URL 包含协议
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        self.url = url

        try:
            self.client = self.Client(url, username, password)
            self.logger.info(f"WordPress XML-RPC 客户端初始化成功: {url}")
        except Exception as e:
            self.logger.error(f"WordPress XML-RPC 客户端初始化失败: {e}")
            raise

    def test_connection(self) -> bool:
        """测试 WordPress XML-RPC 连接"""
        try:
            self.client.call(self.GetTerms('category'))
            self.logger.info("XML-RPC 连接测试成功")
            return True
        except Exception as e:
            self.logger.error(f"XML-RPC 连接测试失败: {e}")
            return False

    def get_all_categories(self) -> list:
        """获取所有分类"""
        try:
            categories = self.client.call(self.GetTerms('category'))
            self.logger.info(f"获取到 {len(categories)} 个分类")
            return categories
        except Exception as e:
            self.logger.error(f"获取分类列表失败: {e}")
            return []

    def get_random_category(self) -> Optional[tuple]:
        """随机选择一个分类，返回 (name, id)"""
        try:
            import random
            categories = self.get_all_categories()

            if not categories:
                self.logger.warning("没有可用的分类")
                return None

            # 过滤掉"未分类"（Uncategorized），通常 ID 为 1
            valid_categories = [cat for cat in categories if int(cat.id) != 1]

            if not valid_categories:
                # 如果只有"未分类"，就使用它
                valid_categories = categories

            random_cat = random.choice(valid_categories)
            self.logger.info(f"随机选择分类: {random_cat.name} (ID: {random_cat.id})")
            return (random_cat.name, int(random_cat.id))

        except Exception as e:
            self.logger.error(f"随机选择分类失败: {e}")
            return None

    def get_category_id(self, category_name: str) -> Optional[int]:
        """获取分类 ID"""
        try:
            categories = self.client.call(self.GetTerms('category'))
            for category in categories:
                if category.name == category_name:
                    self.logger.info(f"找到分类: {category_name} (ID: {category.id})")
                    return int(category.id)

            self.logger.warning(f"未找到分类: {category_name}")
            return None

        except Exception as e:
            self.logger.error(f"获取分类 ID 失败: {e}")
            return None

    def publish_post(
        self,
        title: str,
        content: str,
        category: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[list] = None,
        excerpt: Optional[str] = None
    ) -> Optional[str]:
        """发布文章到 WordPress（XML-RPC）"""
        try:
            self.logger.info(f"准备发布文章 (XML-RPC): {title}")

            post = self.WordPressPost()
            post.title = title
            post.content = content
            post.post_status = status or self.default_status

            if excerpt:
                post.excerpt = excerpt

            # 初始化 terms_names
            post.terms_names = {}

            # 设置分类
            category_name = category or self.default_category
            selected_category_name = None

            if category_name:
                # 如果指定了分类名称，尝试查找
                category_id = self.get_category_id(category_name)
                if category_id:
                    selected_category_name = category_name

            if not selected_category_name:
                # 如果没有指定分类或未找到指定分类，随机选择一个
                self.logger.info("未指定分类或未找到指定分类，将随机选择分类")
                random_cat = self.get_random_category()
                if random_cat:
                    selected_category_name = random_cat[0]  # 使用分类名称

            if selected_category_name:
                post.terms_names['category'] = [selected_category_name]

            # 设置标签
            if tags:
                post.terms_names['post_tag'] = tags

            # 发布文章
            post_id = self.client.call(self.NewPost(post))

            status_text = "已发布" if post.post_status == "publish" else "已保存为草稿"
            self.logger.info(f"文章 {status_text}: {title} (ID: {post_id})")

            return str(post_id)

        except Exception as e:
            self.logger.error(f"发布文章失败 (XML-RPC): {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None


def create_publisher(config: Dict[str, Any]) -> Optional[WordPressPublisherBase]:
    """
    从配置创建 WordPress 发布器

    Args:
        config: WordPress 配置字典

    Returns:
        Optional[WordPressPublisherBase]: 发布器实例，失败返回 None
    """
    logger = logging.getLogger(__name__)

    try:
        if not config.get('enabled', False):
            return None

        # 获取发布方式（默认自动选择）
        api_method = config.get('api_method', 'auto')
        url = config['url']
        username = config['username']
        password = config['password']
        category = config.get('category', '未分类')
        status = config.get('status', 'draft')

        # 自动选择：优先 REST API，失败则尝试 XML-RPC
        if api_method == 'auto':
            logger.info("尝试使用 REST API 连接...")
            try:
                publisher = WordPressRESTPublisher(url, username, password, category, status)
                if publisher.test_connection():
                    logger.info("✓ 使用 REST API 方式发布")
                    return publisher
                else:
                    logger.warning("REST API 连接失败，尝试 XML-RPC...")
            except Exception as e:
                logger.warning(f"REST API 初始化失败: {e}，尝试 XML-RPC...")

            try:
                publisher = WordPressXMLRPCPublisher(url, username, password, category, status)
                if publisher.test_connection():
                    logger.info("✓ 使用 XML-RPC 方式发布")
                    return publisher
                else:
                    logger.error("XML-RPC 连接也失败")
                    return None
            except Exception as e:
                logger.error(f"XML-RPC 初始化失败: {e}")
                return None

        # 强制使用 REST API
        elif api_method == 'rest':
            logger.info("使用 REST API 方式")
            return WordPressRESTPublisher(url, username, password, category, status)

        # 强制使用 XML-RPC
        elif api_method == 'xmlrpc':
            logger.info("使用 XML-RPC 方式")
            return WordPressXMLRPCPublisher(url, username, password, category, status)

        else:
            logger.error(f"不支持的 API 方式: {api_method}")
            return None

    except Exception as e:
        logger.error(f"创建 WordPress 发布器失败: {e}")
        return None
