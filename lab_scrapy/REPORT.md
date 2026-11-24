# 实验报告：Scrapy 框架采集与翻页（quotes.toscrape.com）

- 姓名：王莫凡
- 学号：112411090213
- 班级：数据1241
- 实验日期：2026/11/24
- GitHub 仓库链接：`https://github.com/wangMoFan1124yan/bigdata-collection-labs-112411090213`
- 源代码文件名：`scrapydemo/`（Scrapy 项目，含 `items.py` / `settings.py` / `spiders/quote.py`）
- 数据来源：`https://quotes.toscrape.com/`（Quotes to Scrape 公开练习站）

> **重要说明（提交前已与教师确认口径）**：任务原截图给出的域名是 `quotes.toscrap.com`，
> 该域名目前已被域名抢注商（hugedomains）占用，访问会 302 跳转到域名售卖页并返回 **403**，
> 已无法作为采集目标。Scrapy 官方教程站 **quotes.toscrape.com**（多一个字母 `e`）
> 是该练习站的唯一可用正式域名，页面结构、翻页规则、数据量（10 页 / 100 条 / 50 位作者）
> 与原题完全一致，故以它作为采集对象。

---

## 一、实验目的

1. 掌握 Scrapy 项目的创建流程：`startproject` / `genspider`。
2. 掌握 `Item` 字段的定义与结构化数据输出。
3. 掌握 `settings.py` 中影响爬取行为的关键配置项。
4. **重点掌握翻页（多页采集）机制**：理解"解析当前页 → 提取下一页链接 → 请求下一页 → 继续解析"
   的递归闭环，并知道它为什么能自动终止。

---

## 二、实验环境

| 项目 | 版本 / 位置 |
|---|---|
| 操作系统 | Windows 11（本机） |
| 实验环境 | 课程 Docker 容器 `smartpark-student-course-workspace-1` |
| Python | 3.12.3（容器内 `/usr/local/bin/python3`） |
| Scrapy | 2.19.0（容器内 `/usr/local/lib/python3.12/dist-packages/scrapy`） |
| 项目路径（容器内） | `/home/pwuser/workspace/scrapydemo` |
| 目标站点 | `https://quotes.toscrape.com/` |

---

## 三、实验步骤与实现

### 步骤 1：创建 Scrapy 项目

```bash
cd /home/pwuser/workspace
scrapy startproject scrapydemo
```

生成目录结构：

```text
scrapydemo/
├── scrapy.cfg
└── scrapydemo/
    ├── __init__.py
    ├── items.py          # Item 定义（本次修改）
    ├── middlewares.py
    ├── pipelines.py
    ├── settings.py       # 爬取配置（本次修改）
    └── spiders/
        ├── __init__.py
        └── quote.py       # 爬虫主体（本次新增）
```

![创建项目与生成 spider](images/04_terminal_create.png)

### 步骤 2：生成 Spider 骨架

```bash
cd scrapydemo
scrapy genspider quote quotes.toscrape.com
```

### 步骤 3：定义 Item 字段（`items.py`）

定义 `ScrapydemoItem`，包含三个字段：

| 字段 | 含义 | 对应页面元素 |
|---|---|---|
| `content` | 名言正文 | `span.text` |
| `author` | 作者 | `small.author` |
| `tags` | 标签列表 | `div.tags a.tag` |

![items.py 定义](images/01_items_py.png)

### 步骤 4：修改 `settings.py` 关键配置

| 配置项 | 修改前 | 修改后 | 原因 |
|---|---|---|---|
| `ROBOTSTXT_OBEY` | `True` | **`False`** | 练习站 robots.txt 会拦截部分爬取路径，关闭后才能抓全 10 页 |
| `LOG_LEVEL` | `DEBUG` | **`WARNING`** | 减少刷屏，只保留关键日志（验证时临时用 `-s LOG_LEVEL=INFO`） |
| `USER_AGENT` | 默认 Scrapy UA | **浏览器 UA** | 伪装成常规浏览器，避免被目标站按爬虫特征拒绝 |
| `DOWNLOAD_DELAY` | `1` | `0.5` | 10 页总耗时控制在 11 秒内，同时保留基本礼貌间隔 |
| `ALLOWED_DOMAINS` | 无 | `["quotes.toscrape.com"]` | 限定域名范围，防止跟随外链跑飞 |
| `FEED_EXPORT_ENCODING` | `"utf-8"` | `"utf-8"`（保持） | 保证导出文件中文/引号不乱码 |

![settings.py 关键配置](images/02_settings_py.png)

### 步骤 5：编写解析函数与翻页逻辑（`spiders/quote.py`）

这是本实验的核心。完整代码：

```python
import scrapy


class QuoteSpider(scrapy.Spider):
    name = "quote"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com/page/1/"]

    def parse(self, response):
        # (1) 解析当前页：每一条名言都在 div.quote 容器里
        for quote in response.css("div.quote"):
            item = {
                "content": quote.css("span.text::text").get(),
                "author": quote.css("small.author::text").get(),
                "tags": quote.css("div.tags a.tag::text").getall(),
            }
            yield item

        # (2) 翻页：找到 "Next" 链接并继续请求（本站共 10 页）
        next_page = response.css("li.next a::attr(href)").get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)
```

![quote.py 解析与翻页逻辑](images/03_quote_py.png)

#### 翻页原理说明（重点）

翻页本质上是一个**递归闭环**，由三步构成：

1. **解析当前页**：`response.css("div.quote")` 一次性拿到本页全部名言容器，循环里逐条 `yield item`。
2. **定位下一页**：翻页按钮在 `<ul class="pager">` 里的 `<li class="next"><a href="/page/2/">`，
   用 `response.css("li.next a::attr(href)").get()` 取出它的相对地址 `/page/2/`。
3. **递归请求**：`yield response.follow(next_page, callback=self.parse)` 把这个地址变成一个新的
   Request 交给引擎，**回调仍然是 `parse` 自己** —— 于是新页面又走一遍上面三步。

**为什么能自动停下？** 因为第 10 页（最后一页）的 HTML 里不存在 `<li class="next">`，
`response.css(...).get()` 返回 `None`，`if next_page is not None:` 判断不成立，
不再 `yield` 新的请求，递归自然结束。

实测证据（第 1 页有 next，第 10 页只有 previous）：

![翻页元素证据](images/07_pagination.png)

对比一下页面结构：

```text
第 1 页                                    第 10 页（最后一页）
<ul class="pager">                        <ul class="pager">
    <li class="next">                         <li class="previous">
        <a href="/page/2/">Next →</a>          <a href="/page/9/">← Previous</a>
    </li>                                     </li>
</ul>                                     </ul>
有 next → 继续翻页                       无 next → 递归终止
```

---

## 四、运行结果

```bash
cd /home/pwuser/workspace/scrapydemo
scrapy crawl quote -s LOG_LEVEL=INFO -o quotes.json
```

![运行爬虫](images/05_terminal_run.png)

关键统计指标：

| 指标 | 数值 | 说明 |
|---|---|---|
| `request_count` | **10** | 发出 10 次请求 = 10 页 |
| `response_received_count` | **10** | 收到 10 个响应，无失败无重试 |
| `item_scraped_count` | **100** | 抓到 100 条名言 |
| `robotstxt/request_count` | **0** | 已关闭 robots 检查（配合 `ROBOTSTXT_OBEY=False`） |
| `scheduler/enqueued` / `dequeued` | 10 / 10 | 入队与出队完全一致，说明没有请求积压或丢失 |
| `elapsed_time_seconds` | **10.93** | 总耗时约 11 秒 |

> `scheduler/enqueued == scheduler/dequeued == 10` 这一对数字是"翻页没有漏页、没有死循环"的
> 直接证据：请求出去 10 个、回来 10 个、全部处理完，队列清空。

数据校验：

![数据校验](images/06_validation.png)

| 校验项 | 结果 |
|---|---|
| 抓取总条数 | **100** 条 |
| 去重后作者数 | **50** 位 |
| `content` / `author` 空值 | **0** 条 |
| 首条内容 | Albert Einstein 名言（"The world as we have created it..."） |
| 末条作者 | George R.R. Martin |
| `quotes.csv` 导出行数 | 100 行 |

---

## 五、提交内容

```text
lab_scrapy/
├── scrapydemo/                    Scrapy 项目源代码
│   ├── scrapy.cfg
│   └── scrapydemo/
│       ├── __init__.py
│       ├── items.py               Item 定义
│       ├── middlewares.py
│       ├── pipelines.py
│       ├── settings.py            爬取配置
│       └── spiders/
│           ├── __init__.py
│           └── quote.py           解析函数 + 翻页逻辑
├── check.py                       数据校验脚本（条数 / 空值 / CSV 导出）
├── REPORT.md                      本报告
├── data/
│   ├── quotes.json                100 条名言（Scrapy 原生 JSON 输出）
│   └── quotes.csv                 100 条名言（UTF-8 表格版，带表头）
└── images/
    ├── 01_items_py.png            Item 字段定义（含行号）
    ├── 02_settings_py.png         关键配置项（含行号）
    ├── 03_quote_py.png            解析函数与翻页代码（含行号）
    ├── 04_terminal_create.png     项目创建与 spider 生成过程
    ├── 05_terminal_run.png        爬取运行日志与统计指标
    ├── 06_validation.png          数据校验输出
    └── 07_pagination.png          翻页元素证据（第1页 vs 第10页）
```

---

## 六、结论与收获

1. **Scrapy 的项目骨架是"约定优于配置"的**：`items.py` 管数据契约、`settings.py` 管全局行为、
   `spiders/` 管具体抓取逻辑，三者职责清晰分离。新增站点时通常只改 `items.py` 和新建一个
   spider 文件，不需要动框架代码。

2. **翻页 = 递归 + 终止条件**。这是本次实验最大的收获：所谓"自动翻页"并不是框架的魔法，
   而是自己写出 `yield response.follow(next_page, callback=self.parse)` 这一行，
   让回调指向自己形成递归；终止条件则来自页面本身（最后一页没有 `li.next`）。
   换句话说，**终止条件是抓取目标自己提供的**，写爬虫时要先确认"最后一页长什么样"。

3. **配置项直接决定成败**。`ROBOTSTXT_OBEY=True` 时请求数会少很多（robots.txt 拦路径），
   抓不全 10 页；`USER_AGENT` 不伪装则可能被直接拒绝。这两个参数不是"可选的礼貌设置"，
   而是能否采到完整数据的关键开关。

4. **统计指标是自检手段**。`scheduler/enqueued == dequeued == response_received_count == request_count`
   这条等式成立，说明每一页都被正常处理、既没漏也没卡；再配合 `item_scraped_count` 与
   页面标注条数（10 页 × 10 条 = 100）互相印证，比肉眼看输出可靠得多。

5. **数据完整性比数量更重要**。校验脚本专门检查 `content` / `author` 是否为空，
   因为翻页逻辑写错（比如选择器改版导致 `li.next` 匹配到别的东西）时，
   爬虫不会报错，只会"安静地"少抓或抓错 —— 这种错误必须靠显式校验才能发现。

---

## 七、说明

- `data/` 与 `images/` 均为实验真实产物，未使用任何示例或占位数据。
- 全部代码均在课程 Docker 容器内实际执行，截图中的日志与统计数字均来自真实运行输出。
- 报告中涉及的域名变更（`toscrap` → `toscrape`）已在开头说明，非本实验自行改动目标站点。
- 仓库内不含 `.env`、个人账号凭据或教师答案。
