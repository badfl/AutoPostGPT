#!/usr/bin/env python3
"""
Generator - ChatGPT 文章生成模块
负责生成标题和文章内容
"""

import os
import re
import logging
import requests
from typing import List, Optional, Dict
from openai import OpenAI


class ArticleGenerator:
    """文章生成器类"""

    def __init__(
        self,
        api_key: str = None,
        model: str = "gpt-4-turbo",
        api_base: str = None,
        forbidden_words: List[str] = None
    ):
        """
        初始化文章生成器

        Args:
            api_key: OpenAI API 密钥（如果为 None，从环境变量获取）
            model: 使用的 OpenAI 模型
            api_base: 自定义 API 端点（如果为 None，从环境变量获取）
            forbidden_words: 禁止出现的词汇列表
        """
        self.logger = logging.getLogger(__name__)

        # 获取 API 密钥
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("未找到 OpenAI API 密钥，请设置环境变量 OPENAI_API_KEY 或在初始化时传入")

        # 获取自定义 API 端点
        self.api_base = api_base or os.getenv("OPENAI_API_BASE")

        # 初始化 OpenAI 客户端
        client_kwargs = {"api_key": self.api_key}
        if self.api_base:
            client_kwargs["base_url"] = self.api_base
            self.logger.info(f"使用自定义 API 端点: {self.api_base}")

        self.client = OpenAI(**client_kwargs)
        self.model = model
        self.forbidden_words = forbidden_words or []

        self.logger.info(f"ArticleGenerator 初始化完成，使用模型: {self.model}")
        if self.forbidden_words:
            self.logger.info(f"已设置 {len(self.forbidden_words)} 个禁用词")

    def _check_forbidden_words(self, text: str) -> bool:
        """
        检查文本中是否包含禁用词

        Args:
            text: 要检查的文本

        Returns:
            bool: 包含禁用词返回 True，否则返回 False
        """
        if not self.forbidden_words:
            return False

        text_lower = text.lower()
        for word in self.forbidden_words:
            if word.lower() in text_lower:
                self.logger.warning(f"检测到禁用词: {word}")
                return True
        return False

    def generate_titles(self, keyword: str, n: int = 3, max_retries: int = 3) -> List[str]:
        """
        根据关键词生成 n 个标题，并过滤禁用词

        Args:
            keyword: 关键词
            n: 生成的标题数量
            max_retries: 最大重试次数

        Returns:
            List[str]: 生成的标题列表
        """
        try:
            self.logger.info(f"正在为关键词 '{keyword}' 生成 {n} 个标题...")

            # 构建禁用词提示
            forbidden_hint = ""
            if self.forbidden_words:
                forbidden_hint = f"\n   - 标题中不得包含以下词汇: {', '.join(self.forbidden_words)}"

            # 构建自然写作的禁用词列表（标题版）
            unnatural_title_words = [
                "深入探讨", "揭秘", "探索", "揭开", "完美", "深入剖析",
                "深入分析", "深入了解", "剖析", "深入", "终极指南", "全面解析","带你了解"
            ]

            # 构建提示词
            prompt = f"""请根据以下关键词生成 {n} 个自然风格的中文文章标题。关键词需自然融入，不要堆叠。

关键词: {keyword}

标题风格要求：
1. 标题需自动匹配所属领域（科技、影视、数码、知识科普）的常见写作语气：
   - 科技：理性、直接、信息清晰
   - 数码：偏体验感、真实使用感受
   - 影视：情绪化、更具画面感
   - 科普：易懂、自然、亲切、不装腔
2. 避免AI感很强的词汇: {', '.join(unnatural_title_words)}
3. 不使用营销腔、官方腔的表达，例如：终极指南、深度解析、全面总结这类词汇
4. 可以带些个人感受或真实体验感
5. 标题长度控制在15-30字之间
6. 适合SEO，关键词要自然融入句子里，但不要生硬堆砌关键词{forbidden_hint}
7. 标题要兼容 Google + 百度SEO，但同时保持自然表达。
标题示例（自然 vs 生硬）：
❌ 不好: "深入探讨AI工具的完美应用"
✅ 好: "2025年可免费使用的10多种AI工具"

❌ 不好: "全面解析Python编程技巧"
✅ 好: "【Python教程】《零基础入门学习Python》最新版"

请直接返回 {n} 个标题，每行一个，不要添加编号或其他说明:"""

            for attempt in range(max_retries):
                # 调用 OpenAI API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一个擅长自然写作的内容创作者，能写出真实、有温度、不套路的标题。避免使用AI感强、营销腔的表达方式。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    max_tokens=500
                )

                # 解析返回的标题
                content = response.choices[0].message.content.strip()
                titles = [line.strip() for line in content.split('\n') if line.strip()]

                # 清理可能的编号
                cleaned_titles = []
                for title in titles:
                    # 去除可能的编号
                    title = title.lstrip('0123456789.、 ')
                    if title and not self._check_forbidden_words(title):
                        cleaned_titles.append(title)
                    elif title:
                        self.logger.warning(f"标题包含禁用词，已过滤: {title}")

                # 如果获得足够的标题，返回
                if len(cleaned_titles) >= n:
                    cleaned_titles = cleaned_titles[:n]
                    self.logger.info(f"成功生成 {len(cleaned_titles)} 个标题")
                    for i, title in enumerate(cleaned_titles, 1):
                        self.logger.info(f"  标题 {i}: {title}")
                    return cleaned_titles

                self.logger.warning(f"标题数量不足或包含禁用词，重试 ({attempt + 1}/{max_retries})")

            # 如果所有重试都失败，返回已有的标题
            self.logger.warning(f"经过 {max_retries} 次尝试，仅生成 {len(cleaned_titles)} 个有效标题")
            return cleaned_titles

        except Exception as e:
            self.logger.error(f"生成标题失败: {e}")
            return []

    def generate_image_keywords(self, title: str, count: int = 3) -> List[str]:
        """
        根据文章标题生成适合搜索图片的关键词

        Args:
            title: 文章标题
            count: 需要生成的图片关键词数量

        Returns:
            List[str]: 图片搜索关键词列表
        """
        try:
            self.logger.info(f"正在为标题 '{title}' 生成图片搜索关键词...")

            prompt = f"""请根据以下文章标题，生成 {count} 个适合搜索图片的英文关键词。

文章标题: {title}

要求:
1. 关键词要能准确反映文章的主题和内容
2. 使用简洁的英文单词或短语（2-4个词）
3. 适合在图片搜索引擎中使用
4. 每个关键词应该独特，从不同角度描述主题
5. 直接返回 {count} 个关键词，每行一个，不要添加编号或其他说明

示例：
如果标题是"AI工具推荐"，关键词可以是：
artificial intelligence technology
digital innovation workspace
modern tech tools

请生成关键词:"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的图片搜索专家，擅长将中文主题转化为准确的英文图片搜索关键词。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )

            content = response.choices[0].message.content.strip()
            keywords = [line.strip() for line in content.split('\n') if line.strip()]

            # 清理可能的编号
            cleaned_keywords = []
            for kw in keywords:
                kw = kw.lstrip('0123456789.、 -')
                if kw:
                    cleaned_keywords.append(kw)

            self.logger.info(f"生成了 {len(cleaned_keywords)} 个图片搜索关键词")
            for i, kw in enumerate(cleaned_keywords[:count], 1):
                self.logger.info(f"  关键词 {i}: {kw}")

            return cleaned_keywords[:count]

        except Exception as e:
            self.logger.error(f"生成图片关键词失败: {e}")
            # 返回简化的标题作为备用
            return [title[:50]]

    def generate_image_with_dalle(
        self,
        prompt: str,
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "natural"
    ) -> Optional[str]:
        """
        使用 DALL-E 生成图片

        Args:
            prompt: 图片生成提示词
            model: 模型名称 (dall-e-2 或 dall-e-3)
            size: 图片尺寸
            quality: 图片质量 (standard 或 hd)
            style: 图片风格 (vivid 或 natural)

        Returns:
            Optional[str]: 生成的图片 URL，失败返回 None
        """
        try:
            self.logger.info(f"正在使用 {model} 生成图片...")
            self.logger.info(f"提示词: {prompt}")

            # 构建请求参数
            params = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "n": 1
            }

            # DALL-E 3 特有参数
            if model == "dall-e-3":
                params["quality"] = quality
                params["style"] = style

            response = self.client.images.generate(**params)

            if response.data and len(response.data) > 0:
                image_url = response.data[0].url
                self.logger.info(f"图片生成成功: {image_url}")
                return image_url
            else:
                self.logger.error("图片生成失败：未返回图片数据")
                return None

        except Exception as e:
            self.logger.error(f"DALL-E 生成图片失败: {e}")
            return None

    def generate_image_prompts(self, title: str, count: int = 3) -> List[str]:
        """
        根据文章标题生成 DALL-E 图片提示词

        Args:
            title: 文章标题
            count: 需要生成的提示词数量

        Returns:
            List[str]: DALL-E 提示词列表
        """
        try:
            self.logger.info(f"正在为标题 '{title}' 生成 DALL-E 提示词...")

            prompt = f"""请根据以下文章标题，生成 {count} 个适合 DALL-E 图片生成的英文提示词。

文章标题: {title}

要求:
1. 提示词要详细描述期望的图片场景和风格
2. 使用清晰、具体的英文描述（一句话，15-30个词）
3. 包含主题、风格、构图等元素
4. 适合生成专业、高质量的配图
5. 直接返回 {count} 个提示词，每行一个，不要添加编号或其他说明

示例：
如果标题是"AI工具推荐"，提示词可以是：
A modern workspace with AI technology, featuring holographic displays and futuristic interfaces, professional photography style, clean and minimalist
Digital illustration of artificial intelligence neural network, vibrant colors, abstract tech pattern, high-tech atmosphere
Realistic photo of a person using AI software on laptop, bright office environment, professional business setting

请生成提示词:"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的 DALL-E 提示词工程师，擅长将中文主题转化为高质量的英文图片生成提示词。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()
            prompts = [line.strip() for line in content.split('\n') if line.strip()]

            # 清理可能的编号
            cleaned_prompts = []
            for p in prompts:
                p = p.lstrip('0123456789.、 -')
                if p:
                    cleaned_prompts.append(p)

            self.logger.info(f"生成了 {len(cleaned_prompts)} 个 DALL-E 提示词")

            return cleaned_prompts[:count]

        except Exception as e:
            self.logger.error(f"生成 DALL-E 提示词失败: {e}")
            # 返回简单的英文翻译作为备用
            return [f"Illustration related to: {title}"[:100]]

    def search_images(
        self,
        query: str,
        count: int = 3,
        search_engine: str = "picsum",
        use_smart_keywords: bool = True
    ) -> List[str]:
        """
        从互联网搜索相关图片

        Args:
            query: 搜索关键词（通常是文章标题）
            count: 图片数量
            search_engine: 搜索引擎（picsum, unsplash, pexels, pixabay）
            use_smart_keywords: 是否使用 AI 生成的智能关键词

        Returns:
            List[str]: 图片 URL 列表
        """
        try:
            self.logger.info(f"正在搜索图片: {query} (引擎: {search_engine})")

            # 如果启用智能关键词且不是 picsum，生成专业的英文搜索关键词
            search_queries = [query]
            if use_smart_keywords and search_engine != "picsum":
                smart_keywords = self.generate_image_keywords(query, count)
                if smart_keywords:
                    search_queries = smart_keywords
                    self.logger.info(f"使用智能关键词搜索: {search_queries}")

            if search_engine == "picsum":
                return self._search_picsum(query, count)
            elif search_engine == "unsplash":
                return self._search_unsplash_smart(search_queries, count)
            elif search_engine == "pexels":
                return self._search_pexels_smart(search_queries, count)
            elif search_engine == "pixabay":
                return self._search_pixabay_smart(search_queries, count)
            else:
                self.logger.warning(f"不支持的搜索引擎: {search_engine}，使用 Picsum Photos")
                return self._search_picsum(query, count)

        except Exception as e:
            self.logger.error(f"搜索图片失败: {e}，使用 Picsum Photos")
            return self._search_picsum(query, count)

    def _search_unsplash(self, query: str, count: int) -> List[str]:
        """从 Unsplash 搜索图片"""
        api_key = os.getenv("UNSPLASH_ACCESS_KEY")

        if not api_key:
            # 如果没有 API key，使用 Picsum Photos（可靠的免费图片占位符服务）
            self.logger.warning("未设置 UNSPLASH_ACCESS_KEY，使用 Picsum Photos")
            return self._search_picsum(query, count)

        try:
            headers = {"Authorization": f"Client-ID {api_key}"}
            response = requests.get(
                f"https://api.unsplash.com/search/photos?query={query}&per_page={count}&orientation=landscape",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                images = [photo["urls"]["regular"] for photo in data.get("results", [])[:count]]

                if images:
                    self.logger.info(f"从 Unsplash 获取了 {len(images)} 张图片")
                    return images
                else:
                    self.logger.warning("Unsplash 未返回图片，使用 Picsum Photos")
                    return self._search_picsum(query, count)
            else:
                self.logger.warning(f"Unsplash API 返回错误: {response.status_code}，使用 Picsum Photos")
                return self._search_picsum(query, count)

        except Exception as e:
            self.logger.error(f"Unsplash 搜索失败: {e}，使用 Picsum Photos")
            return self._search_picsum(query, count)

    def _search_pexels(self, query: str, count: int) -> List[str]:
        """从 Pexels 搜索图片（需要 API key）"""
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            self.logger.warning("未设置 PEXELS_API_KEY，使用 Picsum Photos")
            return self._search_picsum(query, count)

        try:
            headers = {"Authorization": api_key}
            response = requests.get(
                f"https://api.pexels.com/v1/search?query={query}&per_page={count}",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                images = [photo["src"]["large"] for photo in data.get("photos", [])[:count]]

                if images:
                    self.logger.info(f"从 Pexels 获取了 {len(images)} 张图片")
                    return images
                else:
                    self.logger.warning("Pexels 未返回图片，使用 Picsum Photos")
                    return self._search_picsum(query, count)
            else:
                self.logger.warning(f"Pexels API 返回错误: {response.status_code}，使用 Picsum Photos")
                return self._search_picsum(query, count)

        except Exception as e:
            self.logger.error(f"Pexels 搜索失败: {e}，使用 Picsum Photos")
            return self._search_picsum(query, count)

    def _search_pixabay(self, query: str, count: int) -> List[str]:
        """从 Pixabay 搜索图片（需要 API key）"""
        api_key = os.getenv("PIXABAY_API_KEY")
        if not api_key:
            self.logger.warning("未设置 PIXABAY_API_KEY，使用 Picsum Photos")
            return self._search_picsum(query, count)

        try:
            response = requests.get(
                f"https://pixabay.com/api/?key={api_key}&q={query}&per_page={count}&image_type=photo",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                images = [hit["largeImageURL"] for hit in data.get("hits", [])[:count]]

                if images:
                    self.logger.info(f"从 Pixabay 获取了 {len(images)} 张图片")
                    return images
                else:
                    self.logger.warning("Pixabay 未返回图片，使用 Picsum Photos")
                    return self._search_picsum(query, count)
            else:
                self.logger.warning(f"Pixabay API 返回错误: {response.status_code}，使用 Picsum Photos")
                return self._search_picsum(query, count)

        except Exception as e:
            self.logger.error(f"Pixabay 搜索失败: {e}，使用 Picsum Photos")
            return self._search_picsum(query, count)

    def _search_picsum(self, query: str, count: int) -> List[str]:
        """
        使用 Picsum Photos 作为备用图片源
        这是一个可靠的免费图片占位符服务，图片可以正常显示
        """
        images = []
        # 使用不同的图片 ID 来获取不同的图片
        # Picsum 提供 1000+ 张高质量图片
        import random
        used_ids = set()

        for i in range(count):
            # 随机选择一个图片 ID (1-1000)
            img_id = random.randint(1, 1000)
            while img_id in used_ids:
                img_id = random.randint(1, 1000)
            used_ids.add(img_id)

            # Picsum Photos URL 格式: https://picsum.photos/id/{id}/800/600
            url = f"https://picsum.photos/id/{img_id}/800/600"
            images.append(url)

        self.logger.info(f"从 Picsum Photos 获取了 {len(images)} 张图片")
        return images

    def _search_unsplash_smart(self, keywords: List[str], count: int) -> List[str]:
        """使用智能关键词从 Unsplash 搜索图片"""
        api_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if not api_key:
            self.logger.warning("未设置 UNSPLASH_ACCESS_KEY，使用 Picsum Photos")
            return self._search_picsum("", count)

        images = []
        for keyword in keywords[:count]:
            try:
                headers = {"Authorization": f"Client-ID {api_key}"}
                response = requests.get(
                    f"https://api.unsplash.com/search/photos?query={keyword}&per_page=1&orientation=landscape",
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("results"):
                        images.append(data["results"][0]["urls"]["regular"])
                        self.logger.info(f"从 Unsplash 找到图片: {keyword}")

            except Exception as e:
                self.logger.error(f"Unsplash 搜索 '{keyword}' 失败: {e}")

        if not images:
            self.logger.warning("Unsplash 未返回图片，使用 Picsum Photos")
            return self._search_picsum("", count)

        self.logger.info(f"从 Unsplash 获取了 {len(images)} 张图片")
        return images

    def _search_pexels_smart(self, keywords: List[str], count: int) -> List[str]:
        """使用智能关键词从 Pexels 搜索图片"""
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            self.logger.warning("未设置 PEXELS_API_KEY，使用 Picsum Photos")
            return self._search_picsum("", count)

        images = []
        for keyword in keywords[:count]:
            try:
                headers = {"Authorization": api_key}
                response = requests.get(
                    f"https://api.pexels.com/v1/search?query={keyword}&per_page=1",
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("photos"):
                        images.append(data["photos"][0]["src"]["large"])
                        self.logger.info(f"从 Pexels 找到图片: {keyword}")

            except Exception as e:
                self.logger.error(f"Pexels 搜索 '{keyword}' 失败: {e}")

        if not images:
            self.logger.warning("Pexels 未返回图片，使用 Picsum Photos")
            return self._search_picsum("", count)

        self.logger.info(f"从 Pexels 获取了 {len(images)} 张图片")
        return images

    def _search_pixabay_smart(self, keywords: List[str], count: int) -> List[str]:
        """使用智能关键词从 Pixabay 搜索图片"""
        api_key = os.getenv("PIXABAY_API_KEY")
        if not api_key:
            self.logger.warning("未设置 PIXABAY_API_KEY，使用 Picsum Photos")
            return self._search_picsum("", count)

        images = []
        for keyword in keywords[:count]:
            try:
                response = requests.get(
                    f"https://pixabay.com/api/?key={api_key}&q={keyword}&per_page=1&image_type=photo",
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("hits"):
                        images.append(data["hits"][0]["largeImageURL"])
                        self.logger.info(f"从 Pixabay 找到图片: {keyword}")

            except Exception as e:
                self.logger.error(f"Pixabay 搜索 '{keyword}' 失败: {e}")

        if not images:
            self.logger.warning("Pixabay 未返回图片，使用 Picsum Photos")
            return self._search_picsum("", count)

        self.logger.info(f"从 Pixabay 获取了 {len(images)} 张图片")
        return images

    def generate_article(
        self,
        title: str,
        template: Optional[str] = None,
        use_template: bool = False,
        word_count: int = 2000,
        image_count: int = 3,
        fetch_real_images: bool = False,
        image_search_engine: str = "unsplash",
        image_mode: str = "search",
        image_generate_model: str = "dall-e-3",
        image_generate_size: str = "1024x1024",
        image_generate_quality: str = "standard",
        image_generate_style: str = "natural",
        max_retries: int = 2
    ) -> str:
        """
        根据标题生成 HTML 格式的文章

        Args:
            title: 文章标题
            template: 可选的文章模板
            use_template: 是否使用模板
            word_count: 目标字数
            image_count: 文章中的配图数量
            fetch_real_images: 是否获取真实图片
            image_search_engine: 图片搜索引擎
            image_mode: 图片模式 (search/generate/mixed)
            image_generate_model: DALL-E 模型
            image_generate_size: 生成图片尺寸
            image_generate_quality: 生成图片质量
            image_generate_style: 生成图片风格
            max_retries: 最大重试次数

        Returns:
            str: HTML 格式的文章内容
        """
        try:
            self.logger.info(f"正在生成文章: {title}")

            # 根据图片模式获取图片
            image_urls = []
            if fetch_real_images and image_count > 0:
                if image_mode == "search":
                    # 模式1: 搜索互联网图片（使用智能关键词）
                    self.logger.info("使用搜索模式获取图片")
                    image_urls = self.search_images(title, image_count, image_search_engine, use_smart_keywords=True)

                elif image_mode == "generate":
                    # 模式2: 使用 DALL-E 生成图片
                    self.logger.info("使用 DALL-E 生成图片")
                    prompts = self.generate_image_prompts(title, image_count)
                    for prompt in prompts:
                        img_url = self.generate_image_with_dalle(
                            prompt,
                            model=image_generate_model,
                            size=image_generate_size,
                            quality=image_generate_quality,
                            style=image_generate_style
                        )
                        if img_url:
                            image_urls.append(img_url)

                elif image_mode == "mixed":
                    # 模式3: 混合模式（部分搜索，部分生成）
                    self.logger.info("使用混合模式获取图片")
                    search_count = image_count // 2
                    generate_count = image_count - search_count

                    # 先搜索一部分
                    if search_count > 0:
                        search_urls = self.search_images(title, search_count, image_search_engine, use_smart_keywords=True)
                        image_urls.extend(search_urls)

                    # 再生成一部分
                    if generate_count > 0:
                        prompts = self.generate_image_prompts(title, generate_count)
                        for prompt in prompts:
                            img_url = self.generate_image_with_dalle(
                                prompt,
                                model=image_generate_model,
                                size=image_generate_size,
                                quality=image_generate_quality,
                                style=image_generate_style
                            )
                            if img_url:
                                image_urls.append(img_url)

            for attempt in range(max_retries):
                # 构建提示词
                prompt = self._build_article_prompt(
                    title,
                    template if use_template else None,
                    word_count,
                    image_count
                )

                # 调用 OpenAI API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个擅长自然写作的内容创作者，能写出真实、有温度、不套路的文章。你的文章应该像真人在分享经验和见解，语气轻松自然，避免使用AI感强、营销腔、官方腔的表达方式。文章使用HTML格式排版。"
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000
                )

                # 获取生成的文章
                article_content = response.choices[0].message.content.strip()

                # 清理可能的完整 HTML 文档结构
                article_content = self._clean_html_structure(article_content)

                # 检查禁用词
                if self._check_forbidden_words(article_content):
                    self.logger.warning(f"文章包含禁用词，重新生成 ({attempt + 1}/{max_retries})")
                    continue

                # 替换图片占位符
                if fetch_real_images and image_urls:
                    article_content = self._replace_image_placeholders(article_content, image_urls)

                self.logger.info(f"文章生成成功，长度: {len(article_content)} 字符")
                return article_content

            # 如果所有重试都因为禁用词失败，返回空
            self.logger.error("文章生成失败：多次尝试后仍包含禁用词")
            return ""

        except Exception as e:
            self.logger.error(f"生成文章失败: {e}")
            return ""

    def _clean_html_structure(self, content: str) -> str:
        """
        清理 HTML 文档结构，只保留文章内容部分

        Args:
            content: 原始内容

        Returns:
            str: 清理后的内容
        """
        # 如果包含完整的 HTML 文档结构，提取 body 内容
        if '<!DOCTYPE' in content or '<html' in content:
            self.logger.warning("检测到完整的 HTML 文档结构，正在清理...")

            # 尝试提取 body 标签内的内容
            body_match = re.search(r'<body[^>]*>(.*)</body>', content, re.DOTALL | re.IGNORECASE)
            if body_match:
                content = body_match.group(1).strip()
                self.logger.info("已提取 body 标签内的内容")

            # 移除常见的文档结构标签
            tags_to_remove = [
                r'<!DOCTYPE[^>]*>',
                r'<html[^>]*>',
                r'</html>',
                r'<head[^>]*>.*?</head>',
                r'<body[^>]*>',
                r'</body>',
                r'<meta[^>]*>',
                r'<title[^>]*>.*?</title>',
            ]

            for tag_pattern in tags_to_remove:
                content = re.sub(tag_pattern, '', content, flags=re.DOTALL | re.IGNORECASE)

            # 清理多余的空行
            content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
            content = content.strip()

            self.logger.info("HTML 结构清理完成")

        # 移除可能的 markdown 代码块标记
        if content.startswith('```html'):
            content = content[7:]  # 移除开头的 ```html
            self.logger.info("移除了开头的 markdown 代码块标记")

        if content.endswith('```'):
            content = content[:-3]  # 移除结尾的 ```
            self.logger.info("移除了结尾的 markdown 代码块标记")

        return content.strip()

    def _replace_image_placeholders(self, content: str, image_urls: List[str]) -> str:
        """
        替换文章中的图片占位符为真实图片 URL

        Args:
            content: 文章内容
            image_urls: 图片 URL 列表

        Returns:
            str: 替换后的内容
        """
        # 查找所有图片占位符
        pattern = r'<img\s+src="?\[IMAGE_PLACEHOLDER[^\]]*\]"?\s+alt="([^"]*)"'
        matches = list(re.finditer(pattern, content))

        # 替换占位符
        for i, match in enumerate(matches):
            if i < len(image_urls):
                alt_text = match.group(1)
                old_tag = match.group(0)
                new_tag = f'<img src="{image_urls[i]}" alt="{alt_text}"'
                content = content.replace(old_tag, new_tag, 1)
                self.logger.info(f"替换图片占位符 {i+1}: {image_urls[i]}")

        return content

    def _build_article_prompt(
        self,
        title: str,
        template: Optional[str],
        word_count: int,
        image_count: int
    ) -> str:
        """
        构建文章生成的提示词

        Args:
            title: 文章标题
            template: 可选的文章模板
            word_count: 目标字数
            image_count: 配图数量

        Returns:
            str: 构建好的提示词
        """
        # 构建禁用词提示
        forbidden_hint = ""
        if self.forbidden_words:
            forbidden_hint = f"\n   - 文章中不得包含以下词汇: {', '.join(self.forbidden_words)}"

        # 构建自然写作的禁用词列表
        unnatural_words = [
            "深入探讨", "揭秘", "探索", "揭开", "完美", "深入剖析",
            "深入分析", "深入了解", "剖析", "深入", "引言", "总结",
            "结语", "概括", "综上所述", "首先", "其次", "最后",
            "从而", "因此可见", "在这篇文章中", "本文将", "让我们一起"
        ]

        prompt = f"""请根据以下标题撰写一篇自然、真实、有温度的中文文章。

标题: {title}

写作风格要求：
1. 像一个真实的人在分享经验和见解，语气轻松自然
2. 使用日常对话的语言，避免官方腔调和营销话术
3. 可以用"我""你""咱们"等第一、第二人称，增加亲切感
4. 适当使用口语化表达，让文章读起来更生动
5. 避免使用这些AI感很强的词汇: {', '.join(unnatural_words)}

内容要求：
1. HTML标签格式排版:
   - 段落使用 <p> 标签
   - 小标题使用 <h2> 或 <h3> 标签（标题要自然、口语化）
   - 重要内容可使用 <strong> 或 <em> 强调
   - 列表使用 <ul> 和 <li> 标签
   - 不要生成完整的 HTML 文档结构（如 <!DOCTYPE>, <html>, <head>, <body> 等标签）
   - 只生成文章内容部分的 HTML

2. 内容质量:
   - 原创内容，有独特见解
   - 逻辑自然流畅，不要生硬分段
   - 目标字数约 {word_count} 字{forbidden_hint}

3. 文章结构（但不要显式标注）:
   - 开头自然切入主题，直接开始讲内容，不要写"在这篇文章中"之类的套话
   - 中间部分自然展开，用 2-4 个小标题组织内容，小标题要口语化、有吸引力
   - 结尾自然收束，可以是建议、展望或个人感受，不要用"总结""综上所述"

4. 图片占位符:
   - 在合适的位置插入 {image_count} 个图片占位符
   - 格式: <img src="[IMAGE_PLACEHOLDER]" alt="相关描述">
   - 图片描述要自然、具体，符合上下文

5. 具体示例（如何自然表达）:
   ❌ 不好: "首先，我们需要了解..."
   ✅ 好: "说到这个，其实..."

   ❌ 不好: "综上所述，我们可以得出结论..."
   ✅ 好: "讲了这么多，你可能已经发现了..."

   ❌ 不好: "本文将深入探讨AI工具的应用..."
   ✅ 好: "最近用了不少AI工具，有些真的挺好用..."
"""

        # 如果提供了模板，添加到提示词中
        if template:
            prompt += f"\n6. 可以参考以下模板结构（但要自然地表达，不要生硬套用）:\n{template}\n"

        prompt += "\n请开始创作（仅返回文章内容的HTML，不要包含 <!DOCTYPE>、<html>、<head>、<body> 等文档结构标签，也不要添加任何说明或注释）:"

        return prompt

    def generate_seo_description(self, title: str, article: str, max_length: int = 160) -> str:
        """
        根据标题和文章生成SEO描述

        Args:
            title: 文章标题
            article: 文章内容
            max_length: 描述最大长度

        Returns:
            str: SEO描述文本
        """
        try:
            self.logger.info(f"正在生成SEO描述...")

            prompt = f"""请根据以下文章标题和内容，生成一段SEO友好的描述文本。

标题: {title}

要求:
1. 描述长度控制在 {max_length} 字符以内
2. 包含关键信息和关键词
3. 吸引用户点击
4. 语言简洁明了
5. 直接返回描述文本，不要包含其他说明

请生成SEO描述:"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个SEO专家，擅长撰写吸引人的meta描述。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=200
            )

            description = response.choices[0].message.content.strip()

            # 检查禁用词
            if self._check_forbidden_words(description):
                self.logger.warning("SEO描述包含禁用词")
                return ""

            self.logger.info(f"SEO描述生成成功")
            return description

        except Exception as e:
            self.logger.error(f"生成SEO描述失败: {e}")
            return ""


# 便捷函数
def create_generator(
    api_key: str = None,
    model: str = "gpt-4-turbo",
    forbidden_words: List[str] = None
) -> ArticleGenerator:
    """
    创建文章生成器实例的便捷函数

    Args:
        api_key: OpenAI API 密钥
        model: 使用的模型
        forbidden_words: 禁用词列表

    Returns:
        ArticleGenerator: 文章生成器实例
    """
    return ArticleGenerator(api_key=api_key, model=model, forbidden_words=forbidden_words)
