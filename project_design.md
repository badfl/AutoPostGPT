# 🧱 项目名称
**AutoPost GPT** — 本地AI内容生成和WordPress自动发布

---

## 🎯 项目目标
构建一个可在本地运行的 Python 程序，实现以下功能：
1. 从关键词文件中读取多个关键词（支持多个关键词用 `|` 分割）。  
2. 根据配置文件定义的“每个关键词生成标题数量”，自动生成标题并用ChatGPT生成对应HTML格式的文章，文章使用图文混排图片获取网络相关图片（可选文章中配图数量）。  
3. 每篇文章生成完后：
   - 保存到本地文件系统（按关键词或时间自动建立分类文件夹）
   - 等待配置文件中设定的时间间隔后再生成下一篇。
4. 支持文章发布到WordPress（可选，通过XML-RPC接口，可以设置保存到草稿还是直接发布，可以设置发布到不同目录）。
5. 所有可变参数（API key、文章格式、时间间隔、输出路径等）都由配置文件定义。

---

## 🧩 核心文件结构

```
AutoPost-GPT/
├── autopost.py              # 主程序入口
├── generator.py             # ChatGPT 文章生成模块
├── publisher.py             # WordPress 发布模块（可选）
├── scheduler.py             # 定时生成与等待逻辑
├── config.yaml              # 配置文件（可自定义文章格式、间隔时间、标题数）
├── keywords.txt             # 关键词文件，关键词之间用 | 分隔
├── output/                  # 本地输出目录（自动分类）
│   ├── AI工具/
│   │   ├── 2025-11-13_01_AI工具.txt
│   │   └── ...
│   ├── AI绘画/
│   │   ├── 2025-11-13_02_AI绘画.txt
│   │   └── ...
├── logs/
│   └── autopost.log
└── .env                     # 环境变量文件（OpenAI/WordPress 凭据）
```

---

## ⚙️ 配置文件示例（config.yaml）

```yaml
# config.yaml
openai_model: "gpt-4-turbo"
title_per_keyword: 3                # 每个关键词生成标题数量
delay_between_posts: 300            # 每篇文章间隔（秒）
save_path: "./output"               # 本地保存路径
save_mode: "keyword"                # 分类方式：keyword 或 date
article_template: |
  <h2>引言</h2>
  <p>{intro}</p>
  <h2>主要内容</h2>
  <p>{body}</p>
  <h2>结语</h2>
  <p>{conclusion}</p>
wordpress:
  enabled: false
  url: "https://yourblog.com/xmlrpc.php"
  username: "admin"
  password: "123456"
```

---

## 📄 关键词文件格式示例（keywords.txt）
一行包含多个关键词，用 `|` 分隔。程序会将每个关键词拆分为独立项，**每个关键词单独生成多篇文章**：

```
AI工具|AI绘画|智能写作|图像生成|Prompt设计
```

上面的配置会拆分为 5 个独立的关键词，每个关键词根据 `title_per_keyword` 配置生成指定数量的文章。

---

## 🧠 核心工作流程

1. **读取关键词文件**
   - 读取所有关键词，用 `|` 分隔的关键词会被拆分为单个关键词
   - 对每个单独的关键词生成配置文件中指定数量的标题
2. **调用 ChatGPT 生成内容**
   - 每个标题生成对应的 HTML 格式文章
   - 可使用配置模板替换结构（如 intro/body/conclusion）
3. **本地保存**
   - 文件只包含纯 HTML 内容
   - 文件命名格式：`标题_时间戳.txt`
   - 若 `save_mode` 为 `keyword`：在以关键词命名的文件夹中保存
   - 若为 `date`：在以日期命名的文件夹中保存
4. **间隔等待**
   - 根据配置文件中 `delay_between_posts` 的值，在生成下一篇文章前暂停
5. **可选：自动发布到 WordPress**
   - 若 `wordpress.enabled = true`，则生成完成后调用 XML-RPC 发布。

---

## 🧩 模块设计

### 1️⃣ generator.py
- 函数：`generate_titles(keyword, n)`
  > 根据关键词生成 n 个标题。
- 函数：`generate_article(title, template)`
  > 使用可选模板和标题生成 HTML 格式文章。

### 2️⃣ scheduler.py
- 函数：`wait_for_next(delay)`
  > 根据配置的延迟时间等待下一篇生成。
- 函数：`run_batch_generation()`
  > 主循环逻辑。

### 3️⃣ autopost.py
- 从命令行启动：  
  ```
  python autopost.py
  ```
- 调用 generator 与 scheduler 模块完成整个任务。

---

## 🧠 ChatGPT 生成逻辑说明

> prompt 示例：
> “请根据以下标题生成一篇中文原创文章，使用HTML标签格式排版：
> - 段落使用<p>；
> - 小标题使用<h2>；
> - 内容风格参考新闻资讯类；
> 标题：{title}
> 模板参考：
> {template}
> 字数约2000字。”

---

## 💾 本地文件命名规则

| 分类方式 | 文件夹名称 | 文件名格式 |
|-----------|-------------|-------------|
| keyword | 对应关键词（如 AI绘画） | SEO生成的标题`从AI绘画到智能写作：全面了解最新AI工具如何激发创意_2025-11-13_01.txt` |
| date | 日期文件夹（如 2025-11-13/） | `01_AI绘画.txt` |

---

## 🧰 日志与异常处理
- 日志路径：`logs/autopost.log`
- 记录内容：
  - 每次生成标题/文章的关键词
  - 生成时间、保存路径、状态
  - 错误堆栈信息

---


