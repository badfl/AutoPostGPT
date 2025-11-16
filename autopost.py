#!/usr/bin/env python3
"""
AutoPost GPT - 主程序入口
自动内容生成与 WordPress 发布工具
"""

import sys
import os
import yaml
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from generator import ArticleGenerator
from publisher import create_publisher

# 加载环境变量
load_dotenv()


class AutoPost:
    """主程序类，处理命令行输入和配置管理"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化 AutoPost

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.generator = None  # 文章生成器实例
        self.publisher = None  # WordPress 发布器实例
        self.setup_logging()

    def setup_logging(self):
        """设置日志系统"""
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # 配置日志格式
        log_file = log_dir / "autopost.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 60)
        self.logger.info("AutoPost GPT 启动")
        self.logger.info("=" * 60)

    def load_config(self) -> bool:
        """
        加载配置文件

        Returns:
            bool: 加载成功返回 True，否则返回 False
        """
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                self.logger.error(f"配置文件不存在: {self.config_path}")
                return False

            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)

            self.logger.info(f"成功加载配置文件: {self.config_path}")
            return True

        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return False

    def load_keywords(self, keywords_path: str = "keywords.txt") -> list:
        """
        从文件中加载关键词

        Args:
            keywords_path: 关键词文件路径

        Returns:
            list: 关键词列表（将用|分隔的关键词拆分为单个关键词）
        """
        try:
            keywords_file = Path(keywords_path)
            if not keywords_file.exists():
                self.logger.error(f"关键词文件不存在: {keywords_path}")
                return []

            all_keywords = []
            with open(keywords_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        # 将用 | 分隔的关键词拆分为单个关键词
                        keywords_in_line = [kw.strip() for kw in line.split('|') if kw.strip()]
                        all_keywords.extend(keywords_in_line)

            self.logger.info(f"成功加载 {len(all_keywords)} 个关键词")
            return all_keywords

        except Exception as e:
            self.logger.error(f"加载关键词文件失败: {e}")
            return []

    def validate_config(self) -> bool:
        """
        验证配置文件的必需参数

        Returns:
            bool: 配置有效返回 True，否则返回 False
        """
        required_fields = [
            'openai_model',
            'title_per_keyword',
            'delay_between_posts',
            'save_path',
            'save_mode'
        ]

        for field in required_fields:
            if field not in self.config:
                self.logger.error(f"配置文件缺少必需字段: {field}")
                return False

        # 验证 save_mode 的值
        if self.config['save_mode'] not in ['keyword', 'date']:
            self.logger.error(f"save_mode 必须是 'keyword' 或 'date'")
            return False

        return True

    def create_output_directory(self, keyword: str = None) -> Path:
        """
        根据配置创建输出目录

        Args:
            keyword: 关键词

        Returns:
            Path: 输出目录路径
        """
        base_path = Path(self.config['save_path'])

        if self.config['save_mode'] == 'keyword':
            # 使用关键词作为文件夹名
            if keyword:
                folder_name = keyword
            else:
                folder_name = 'default'
            output_dir = base_path / folder_name
        else:  # date mode
            # 使用日期作为文件夹名
            today = datetime.now().strftime('%Y-%m-%d')
            output_dir = base_path / today

        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def display_welcome(self):
        """显示欢迎信息"""
        print("\n" + "=" * 60)
        print("  AutoPost GPT - 自动内容生成与发布工具")
        print("=" * 60)
        print()

    def display_config_summary(self):
        """显示配置摘要"""
        print("\n配置摘要:")
        print("-" * 60)
        print(f"  模型: {self.config.get('openai_model', 'N/A')}")
        print(f"  每个关键词生成标题数: {self.config.get('title_per_keyword', 'N/A')}")
        print(f"  文章间隔时间: {self.config.get('delay_between_posts', 'N/A')} 秒")
        print(f"  保存路径: {self.config.get('save_path', 'N/A')}")
        print(f"  保存模式: {self.config.get('save_mode', 'N/A')}")

        if self.config.get('wordpress', {}).get('enabled', False):
            print(f"  WordPress 发布: 已启用")
            print(f"  WordPress URL: {self.config.get('wordpress', {}).get('url', 'N/A')}")
        else:
            print(f"  WordPress 发布: 未启用")
        print("-" * 60)
        print()

    def prompt_continue(self) -> bool:
        """
        提示用户是否继续

        Returns:
            bool: 用户选择继续返回 True，否则返回 False
        """
        while True:
            response = input("是否继续执行? (y/n): ").strip().lower()
            if response in ['y', 'yes', '是']:
                return True
            elif response in ['n', 'no', '否']:
                return False
            else:
                print("请输入 y 或 n")

    def save_article(self, keyword: str, title: str, content: str, index: int) -> bool:
        """
        保存文章到本地文件

        Args:
            keyword: 关键词
            title: 文章标题
            content: 文章内容（纯 HTML）
            index: 文章序号

        Returns:
            bool: 保存成功返回 True，否则返回 False
        """
        try:
            # 创建输出目录
            output_dir = self.create_output_directory(keyword)

            # 生成文件名：使用标题+时间
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # 清理标题中的非法文件名字符
            safe_title = title.replace('/', '_').replace('\\', '_').replace(':', '_')
            safe_title = safe_title.replace('*', '_').replace('?', '_').replace('"', '_')
            safe_title = safe_title.replace('<', '_').replace('>', '_').replace('|', '_')

            # 限制文件名长度
            if len(safe_title) > 50:
                safe_title = safe_title[:50]

            filename = f"{safe_title}_{timestamp}.txt"
            filepath = output_dir / filename

            # 只保存纯 HTML 内容
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"文章已保存: {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"保存文章失败: {e}")
            return False

    def generate_and_save_article(
        self,
        keyword: str,
        title: str,
        index: int,
        total: int
    ) -> bool:
        """
        生成并保存单篇文章

        Args:
            keyword: 关键词
            title: 文章标题
            index: 当前文章序号
            total: 总文章数

        Returns:
            bool: 成功返回 True，否则返回 False
        """
        try:
            print(f"\n[{index}/{total}] 正在生成文章...")
            print(f"  关键词: {keyword}")
            print(f"  标题: {title}")

            # 生成文章
            template = self.config.get('article_template')
            use_template = self.config.get('use_template', False)
            word_count = self.config.get('word_count', 2000)
            image_count = self.config.get('image_count', 3)
            fetch_real_images = self.config.get('fetch_real_images', False)
            image_search_engine = self.config.get('image_search_engine', 'unsplash')
            image_mode = self.config.get('image_mode', 'search')
            image_generate_model = self.config.get('image_generate_model', 'dall-e-3')
            image_generate_size = self.config.get('image_generate_size', '1024x1024')
            image_generate_quality = self.config.get('image_generate_quality', 'standard')
            image_generate_style = self.config.get('image_generate_style', 'natural')

            article_content = self.generator.generate_article(
                title=title,
                template=template,
                use_template=use_template,
                word_count=word_count,
                image_count=image_count,
                fetch_real_images=fetch_real_images,
                image_search_engine=image_search_engine,
                image_mode=image_mode,
                image_generate_model=image_generate_model,
                image_generate_size=image_generate_size,
                image_generate_quality=image_generate_quality,
                image_generate_style=image_generate_style
            )

            if not article_content:
                print("  ❌ 文章生成失败")
                return False

            print(f"  ✓ 文章生成成功 ({len(article_content)} 字符)")

            # 保存文章到本地
            if self.save_article(keyword, title, article_content, index):
                print(f"  ✓ 文章已保存到本地")
            else:
                print(f"  ❌ 文章保存失败")
                return False

            # 如果启用了 WordPress 发布，则发布文章
            if self.publisher:
                print(f"  正在发布到 WordPress...")
                post_id = self.publish_to_wordpress(title, article_content, keyword)
                if post_id:
                    print(f"  ✓ 已发布到 WordPress (ID: {post_id})")
                else:
                    print(f"  ⚠️  WordPress 发布失败（本地文件已保存）")
                    # 注意：即使 WordPress 发布失败，我们仍然返回 True，因为本地保存成功了

            return True

        except Exception as e:
            self.logger.error(f"生成并保存文章失败: {e}")
            print(f"  ❌ 错误: {e}")
            return False

    def publish_to_wordpress(
        self,
        title: str,
        content: str,
        keyword: str
    ) -> Optional[str]:
        """
        发布文章到 WordPress

        Args:
            title: 文章标题
            content: 文章内容
            keyword: 关键词（可用作标签）

        Returns:
            Optional[str]: 文章 ID，失败返回 None
        """
        try:
            wp_config = self.config.get('wordpress', {})
            category = wp_config.get('category', '默认分类')
            status = wp_config.get('status', 'draft')

            # 使用关键词作为标签
            tags = [keyword] if keyword else None

            post_id = self.publisher.publish_post(
                title=title,
                content=content,
                category=category,
                status=status,
                tags=tags
            )

            if post_id:
                self.logger.info(f"文章已发布到 WordPress: {title} (ID: {post_id})")
                return post_id
            else:
                self.logger.error(f"WordPress 发布失败: {title}")
                return None

        except Exception as e:
            self.logger.error(f"发布到 WordPress 时出错: {e}")
            return None

    def process_keywords(self, keywords: List[str]) -> int:
        """
        处理所有关键词，生成文章

        Args:
            keywords: 关键词列表

        Returns:
            int: 成功生成的文章数
        """
        success_count = 0
        total_articles = len(keywords) * self.config['title_per_keyword']
        article_index = 0

        for keyword in keywords:
            self.logger.info(f"开始处理关键词: {keyword}")
            print(f"\n{'=' * 60}")
            print(f"处理关键词: {keyword}")
            print(f"{'=' * 60}")

            # 生成标题
            print(f"正在生成 {self.config['title_per_keyword']} 个标题...")
            titles = self.generator.generate_titles(
                keyword=keyword,
                n=self.config['title_per_keyword']
            )

            if not titles:
                self.logger.warning(f"关键词 '{keyword}' 的标题生成失败，跳过")
                print("❌ 标题生成失败，跳过该关键词")
                continue

            print(f"✓ 成功生成 {len(titles)} 个标题")

            # 对每个标题生成文章
            for i, title in enumerate(titles, 1):
                article_index += 1

                # 生成并保存文章
                if self.generate_and_save_article(
                    keyword=keyword,
                    title=title,
                    index=article_index,
                    total=total_articles
                ):
                    success_count += 1

                # 如果不是最后一篇文章，等待指定时间
                if article_index < total_articles:
                    delay = self.config['delay_between_posts']
                    print(f"\n  等待 {delay} 秒后继续...")
                    time.sleep(delay)

        return success_count

    def run(self):
        """主运行流程"""
        # 显示欢迎信息
        self.display_welcome()

        # 加载配置文件
        print("正在加载配置文件...")
        if not self.load_config():
            print("❌ 配置文件加载失败，程序退出")
            return 1

        # 验证配置
        if not self.validate_config():
            print("❌ 配置验证失败，程序退出")
            return 1

        print("✓ 配置文件加载成功")

        # 初始化文章生成器
        print("\n正在初始化文章生成器...")
        try:
            forbidden_words = self.config.get('forbidden_words', [])
            self.generator = ArticleGenerator(
                model=self.config['openai_model'],
                forbidden_words=forbidden_words
            )
            print("✓ 文章生成器初始化成功")
            if forbidden_words:
                print(f"  已设置 {len(forbidden_words)} 个禁用词")
        except Exception as e:
            print(f"❌ 文章生成器初始化失败: {e}")
            self.logger.error(f"初始化生成器失败: {e}")
            return 1

        # 初始化 WordPress 发布器（如果启用）
        wp_config = self.config.get('wordpress', {})
        if wp_config.get('enabled', False):
            print("\n正在初始化 WordPress 发布器...")
            try:
                self.publisher = create_publisher(wp_config)
                if self.publisher and self.publisher.test_connection():
                    print("✓ WordPress 发布器初始化成功")
                    print(f"  目标站点: {wp_config['url']}")
                    print(f"  发布状态: {wp_config.get('status', 'draft')}")
                else:
                    print("⚠️  WordPress 连接失败，将仅保存到本地")
                    self.publisher = None
            except Exception as e:
                print(f"⚠️  WordPress 发布器初始化失败: {e}")
                print("  将仅保存文章到本地")
                self.logger.error(f"初始化 WordPress 发布器失败: {e}")
                self.publisher = None
        else:
            print("\n✓ WordPress 发布功能未启用，将仅保存到本地")

        # 加载关键词
        print("\n正在加载关键词文件...")
        keywords = self.load_keywords()
        if not keywords:
            print("❌ 关键词文件加载失败或为空，程序退出")
            return 1

        print(f"✓ 成功加载 {len(keywords)} 个关键词组")

        # 显示关键词列表
        # print("\n关键词列表:")
        # for i, kw in enumerate(keywords, 1):
        #     print(f"  {i}. {kw}")

        # 显示配置摘要
        self.display_config_summary()

        # 计算总共要生成的文章数
        total_articles = len(keywords) * self.config['title_per_keyword']
        total_time_minutes = (total_articles - 1) * self.config['delay_between_posts'] / 60

        print(f"预计生成:")
        print(f"  - 总文章数: {total_articles} 篇")
        print(f"  - 预计总耗时: {total_time_minutes:.1f} 分钟 (不含生成时间)")
        print()

        # 询问用户是否继续
        if not self.prompt_continue():
            print("\n程序已取消")
            return 0

        print("\n开始生成文章...")
        print("=" * 60)

        # 开始批量生成文章
        start_time = datetime.now()
        self.logger.info("开始批量生成文章")

        success_count = self.process_keywords(keywords)

        # 完成统计
        end_time = datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()

        print("\n" + "=" * 60)
        print("生成完成!")
        print("=" * 60)
        print(f"成功生成: {success_count}/{total_articles} 篇")
        print(f"总耗时: {elapsed_time/60:.1f} 分钟")
        print(f"输出目录: {self.config['save_path']}")
        print("=" * 60)

        self.logger.info(f"批量生成完成: 成功 {success_count}/{total_articles} 篇")
        self.logger.info(f"总耗时: {elapsed_time:.1f} 秒")

        return 0


def main():
    """主入口函数"""
    # 检查命令行参数
    config_path = "config.yaml"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    # 创建并运行 AutoPost 实例
    app = AutoPost(config_path)
    exit_code = app.run()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
