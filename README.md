# AutoPost GPT AI驱动的自动内容生成与发布工具 - 使用 ChatGPT/DALL-E自动生成高质量中文文章并发布到WordPress

## ✨ 功能特点

### 🤖 智能内容生成
- **自然写作风格**：避免 AI 感强的套话和官腔，生成真实、有温度的文章
- **SEO 优化**：自动生成 SEO 友好的文章标题和内容
- **HTML 格式**：自动生成规范的 HTML 格式文章，支持段落、标题、列表等
- **可定制**：支持自定义文章模板、字数、禁用词过滤

### 🖼️ 智能配图（两种方式）
#### 方式1：智能搜索互联网图片（免费）
- AI 自动生成专业英文搜索关键词
- 从 Unsplash/Pexels/Pixabay 搜索相关高质量图片
- 完全免费，图片主题高度匹配

#### 方式2：DALL-E AI 生成图片
- 使用 OpenAI DALL-E 2/3 生成定制化图片
- 图片完美匹配文章主题
- 支持多种尺寸、质量、风格设置

### 📤 WordPress 自动发布
- 支持 REST API 和 XML-RPC 两种发布方式
- 自动选择或随机选择 WordPress 分类
- 支持草稿和直接发布两种模式
- 自动添加标签和分类

### 💾 本地保存管理
- 按关键词或日期自动分类保存
- 只保存纯 HTML 内容，便于使用
- 完整的日志记录

### 🎯 批量处理
- 支持批量关键词处理
- 可设置文章生成间隔时间
- 自动重试机制

## 📦 安装

### 1. 克隆项目

```bash
git clone https://github.com/badfl/AutoPostGPT
cd autopost-gpt
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置 API 密钥：

```bash
# OpenAI API（必需）- 使用神马中转API
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://api.whatai.cc/v1

# 图片搜索 API（可选，使用搜索模式时需要）
UNSPLASH_ACCESS_KEY=your_unsplash_key    # 推荐，免费
PEXELS_API_KEY=your_pexels_key           # 可选
PIXABAY_API_KEY=your_pixabay_key         # 可选
```

#### 关于神马中转API

**神马中转API** 是一个稳定可靠的 OpenAI API 中转服务：

- **官网**：[https://api.whatai.cc](https://api.whatai.cc)
- **优势**：
  - ✅ 国内访问稳定快速，无需科学上网
  - ✅ 支持多种主流 AI 模型（GPT-4、Claude、DALL-E 等）
  - ✅ 价格透明，按量付费
  - ✅ 提供详细的使用文档和支持

- **支持的模型**：
  - GPT 系列：`gpt-4o-mini`, `gpt-4`, `gpt-3.5-turbo` 等
  - Claude 系列：`claude-3-sonnet-20240229`, `claude-3-opus` 等
  - DALL-E 系列：`dall-e-2`, `dall-e-3`
  - 查看完整模型列表：[https://api.whatai.cc/models](https://api.whatai.cc/models)

- **获取 API Key**：
  1. 访问 [https://api.whatai.cc](https://api.whatai.cc) 注册账号
  2. 充值（支持支付宝、微信）
  3. 在控制台获取 API Key
  4. 将 API Key 填入 `.env` 文件

- **使用方法**：
  ```bash
  # .env 文件配置
  OPENAI_API_KEY=sk-xxxxx               # 你的神马 API Key
  OPENAI_API_BASE=https://api.whatai.cc/v1  # 神马中转地址
  ```

  ```yaml
  # config.yaml 配置
  openai_model: "gpt-4o-mini"  # 或其他支持的模型
  ```

### 4. 配置项目

编辑 `config.yaml` 文件，根据需要调整配置参数（详见配置说明）

### 5. 准备关键词

编辑 `keywords.txt` 文件，每行一个或多个关键词（用 `|` 分隔）

## 🚀 使用方法

### 基本使用

```bash
python3 autopost.py
```

### 使用自定义配置文件

```bash
python3 autopost.py custom_config.yaml
```

### 测试 WordPress 连接

```bash
python3 test_wordpress.py
```

### 测试随机分类功能

```bash
python3 test_random_category.py
```

## ⚙️ 配置说明

### config.yaml 完整配置

```yaml
# OpenAI 设置
openai_model: "gpt-4o-mini"  # 可选：gpt-4, claude-3-sonnet-20240229 等

# 生成设置
title_per_keyword: 2          # 每个关键词生成标题数量
delay_between_posts: 60       # 每篇文章间隔（秒）
word_count: 2000              # 文章字数
image_count: 3                # 文章中的图片数量

# 模板设置
use_template: false           # 是否使用文章模板

# 内容过滤
forbidden_words:              # 禁用词列表
  - "违禁词示例"

# 图片设置
image_mode: "search"          # 图片模式：search（搜索）/generate（生成）/mixed（混合）
fetch_real_images: true       # 是否获取真实图片
image_search_engine: "unsplash"  # 搜索引擎：unsplash/pexels/pixabay/picsum

# DALL-E 图片生成设置（当 image_mode 为 generate 或 mixed 时使用）
image_generate_model: "dall-e-3"      # dall-e-2 或 dall-e-3
image_generate_size: "1024x1024"      # 图片尺寸
image_generate_quality: "standard"    # standard 或 hd（仅 dall-e-3）
image_generate_style: "natural"       # vivid 或 natural（仅 dall-e-3）

# 保存设置
save_path: "./output"         # 本地保存路径
save_mode: "keyword"          # 分类方式：keyword 或 date

# WordPress 发布设置
wordpress:
  enabled: true               # 是否启用 WordPress 发布
  api_method: "xmlrpc"        # 发布方式：auto/rest/xmlrpc
  url: "https://yourblog.com/xmlrpc.php"
  username: "your_username"
  password: "your_password"
  category: ""                # 留空则随机选择分类
  status: "draft"             # draft 或 publish
```

### 图片模式详解

#### 🔍 search 模式（推荐，免费）
使用 AI 生成智能关键词，从图片网站搜索相关图片。

**优势**：
- 完全免费（Unsplash 提供免费 API）
- 真实高质量摄影作品
- 速度快（1-2秒）

**配置**：
```yaml
image_mode: "search"
image_search_engine: "unsplash"  # 需要 UNSPLASH_ACCESS_KEY
```

#### 🎨 generate 模式（付费，最佳匹配）
使用 DALL-E 生成完全定制的图片。

**优势**：
- 图片完美匹配文章主题
- 独一无二的原创图片
- 无版权问题

**配置**：
```yaml
image_mode: "generate"
image_generate_model: "dall-e-3"
image_generate_quality: "standard"
```

#### ⚖️ mixed 模式（平衡方案）
结合搜索和生成两种方式。

**配置**：
```yaml
image_mode: "mixed"
image_count: 4  # 前2张搜索，后2张生成
```

### keywords.txt 格式

每行可以包含多个用 `|` 分隔的关键词：

```
AI工具|AI绘画|智能写作
机器学习|深度学习
Web开发
```

程序会将它们拆分为独立关键词，每个关键词单独生成文章。

## 📁 文件结构

```
autopost/
├── autopost.py              # 主程序入口
├── generator.py             # AI 文章和图片生成模块
├── publisher.py             # WordPress 发布模块
├── config.yaml              # 配置文件
├── keywords.txt             # 关键词文件
├── requirements.txt         # Python 依赖
├── .env                     # 环境变量（需自行创建）
├── .env.example             # 环境变量示例
├── test_wordpress.py        # WordPress 连接测试
├── test_random_category.py  # 随机分类测试
├── output/                  # 文章输出目录（自动创建）
│   ├── AI工具/
│   ├── 机器学习/
│   └── ...
└── logs/                    # 日志目录（自动创建）
    └── autopost.log
```

## 📝 输出格式

生成的文章保存为 `.txt` 文件，**只包含纯 HTML 内容**。

**文件命名**：`标题_时间戳.txt`

**示例**：`AI工具的未来发展_20251116_143020.txt`

**内容示例**：
```html
<p>说到AI工具，最近确实有不少好用的...</p>

<h2>为什么这些工具值得尝试</h2>

<p>用了几个月下来，我发现...</p>

<img src="https://images.unsplash.com/..." alt="AI technology workspace">

<p>特别是在处理日常工作时...</p>
```

## 🎯 核心特性说明

### 1. 自然写作风格

系统会**自动避免**这些 AI 感强的表达：
- ❌ "深入探讨"、"揭秘"、"完美"
- ❌ "引言"、"总结"、"综上所述"
- ❌ "首先"、"其次"、"最后"
- ❌ "在这篇文章中"、"本文将"

改用**自然口语化**的表达：
- ✅ "说到这个，其实..."
- ✅ "用了几个月下来..."
- ✅ "讲了这么多，你可能已经发现了..."

### 2. 智能图片匹配

**传统方式**：直接用中文标题搜索 → 图片不相关

**AutoPost 方式**：
1. AI 分析文章标题
2. 生成专业的英文搜索关键词
3. 使用这些关键词搜索高质量图片

**示例**：

文章标题：`AI工具推荐：2024年值得使用的10款工具`

生成的搜索关键词：
- `artificial intelligence technology`
- `digital innovation workspace`
- `modern tech tools`

搜索结果：3张高度相关的专业图片

### 3. WordPress 随机分类

如果不指定分类（`category: ""`），系统会：
1. 获取 WordPress 所有分类
2. 过滤掉"未分类"
3. 随机选择一个分类发布

这样可以让文章分布更均匀。

## 🔧 常见问题

### Q: 如何获取 Unsplash API Key？
A:
1. 访问 [https://unsplash.com/developers](https://unsplash.com/developers)
2. 注册并创建应用
3. 复制 Access Key
4. 免费额度：50 请求/小时

### Q: DALL-E 生成图片需要多久？
A: DALL-E 3 通常需要 10-30 秒/张，DALL-E 2 约 5-10 秒/张。

### Q: 如何降低成本？
A:
1. 使用 `image_mode: "search"`（完全免费）
2. 使用 `gpt-4o-mini` 模型（更便宜）
3. 减少 `image_count` 数量
4. 使用 `dall-e-2` 替代 `dall-e-3`

### Q: WordPress 发布失败怎么办？
A:
1. 运行 `python3 test_wordpress.py` 测试连接
2. 检查 URL、用户名、密码是否正确
3. 如果 REST API 失败，尝试 XML-RPC
4. 查看日志文件 `logs/autopost.log`

### Q: 为什么没有自动发布到 WordPress？
A:
1. 检查 `config.yaml` 中 `wordpress.enabled` 是否为 `true`
2. 运行测试脚本确认连接正常
3. 查看程序启动时的提示信息
4. 检查日志中的错误信息

### Q: 神马中转API 和官方 OpenAI API 有什么区别？
A:
- **访问方式**：神马可在国内直接访问，无需科学上网
- **价格**：神马提供竞争力的价格，支持国内支付
- **支持**：神马提供中文客服和技术支持
- **兼容性**：完全兼容 OpenAI API 格式
- **额外模型**：支持 Claude 等其他大模型


## ⚠️ 注意事项

1. **API 额度**：确保你的 API Key 有足够额度
2. **速率限制**：建议设置 `delay_between_posts: 60` 避免限流
3. **测试优先**：先用少量关键词测试，确认无误后再批量生成
4. **WordPress 权限**：确保 WordPress 用户有发布文章的权限
5. **图片版权**：
   - 搜索模式：遵守各平台的使用协议（Unsplash 允许免费商用）
   - 生成模式：DALL-E 生成的图片归你所有

## 📦 依赖项

```
python >= 3.7
openai >= 1.0.0
pyyaml >= 6.0
python-dotenv >= 1.0.0
requests >= 2.28.0
python-wordpress-xmlrpc >= 2.3  # WordPress 发布（可选）
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

如果这个项目对你有帮助，请给个 ⭐️ Star！

## 📄 许可证

MIT License

## 🔗 相关链接

- [神马中转API](https://api.whatai.cc) - 稳定的 OpenAI API 中转服务


## 📮 联系方式

如有问题或建议，欢迎提交 Issue。
