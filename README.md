# 大数据采集与处理实验

- 姓名：王莫凡
- 学号：112411090213
- 班级：数据1241

## 实验目录

| 实验 | 内容 | 目录 |
|---|---|---|
| Lab 1 | 静态页面与 API 数据采集 | [`lab01/`](lab01/) |
| Lab 2 | 房源网页采集与 MySQL 入库存储 | [`lab02/`](lab02/) |
| Lab 3 | Scrapy 框架采集与翻页（quotes.toscrape.com） | [`lab_scrapy/`](lab_scrapy/) |

## Lab 1 提交内容

```text
lab01/
├── lab1_html_api.ipynb        采集代码（Docker 容器内 JupyterLab 已完整执行）
├── REPORT.md                  实验报告
├── data/
│   ├── companies.json         60 条企业记录
│   └── devices.json           5000 条设备记录
└── images/
    ├── 01_device_api.png      设备 API 发现证据（DevTools / Network）
    ├── 02_company_source.png  企业页静态加载证据（查看网页源代码）
    ├── 03_company_next.png    "下一页"元素（DevTools / Elements）
    └── 04_validation.png      最终验证结果（JupyterLab 输出）
```

## Lab 2 提交内容

```text
lab02/
├── anjuke.ipynb               阶段二采集代码（容器内 JupyterLab 已完整执行，含 10 页翻页与去重输出）
├── anjuke.py                  阶段二采集脚本（与 notebook 等价，便于命令行复现）
├── insert_mysql.ipynb         阶段三入库代码（容器内已完整执行：0 → 498 条，逐字段比对 0 处不一致）
├── insert_mysql.py            阶段三入库脚本（与 notebook 等价，含事务与唯一索引逻辑）
├── REPORT.md                  实验报告（阶段一 / 二 / 三，含 18 张真实截图）
├── data/
│   └── houseinfo.csv          498 条房源记录（UTF-8-SIG，8 个业务字段）
└── images/                    18 张实验过程截图
    ├── 00_source_page.png         教学站首页原貌
    ├── 01_field_mapping.png       8 个字段定位对照表
    ├── 02_csv_header_and_rows.png CSV 表头与数据
    ├── 03_row_count.png           采集 600 条 → 去重后 498 条
    ├── 04_phase3_result.png       第三阶段运行结果（0 → 498，重跑新增 0）
    ├── 05_phase3_code.png         ensure_unique_index() 与 SHOW INDEX 验证
    ├── 06_unique_index_before.png 建唯一索引前（仅 PRIMARY）
    ├── 07_unique_index_after.png  8 字段联合唯一索引（Non_unique=0）
    ├── 08_mysql_count.png         SELECT COUNT(*) = 498
    ├── 09_mysql_samples.png       id 为 1 / 250 / 498 的三条样本
    ├── 10_code_read_csv.png       read_csv() 代码
    ├── 11_code_insert_rollback.png 批量插入 / 事务提交回滚代码
    ├── 12_code_parse_row.png      parse_row() 字段解析代码
    ├── 13_code_pagination.png     翻页逻辑代码
    ├── 14_code_save_csv.png       CSV 保存与回读校验代码
    ├── 15_start_mysql_pass.png    start-mysql.bat 启动成功提示
    ├── 16_show_tables_describe.png 建表结果（SHOW TABLES / DESCRIBE）
    └── 17_elements_selector.png   Elements 面板选择器推导
```

### Lab 2 关键结果

- 数据来源：在线教学站 `http://www.bspider.top/anjuke/`，状态码 200，`div.property` 每页匹配 60 条
- 采集 10 页共 600 条，Python 侧按 8 字段完全相同去重，删除 102 条，剩余 **498 条**
- MySQL 目标：`smartpark_lab.houseinfo`，入库前 0 条 → 入库后 **498 条**
- 逐字段比对数据库与 CSV：不一致 **0** 处；独立重跑新增 **0** 条
- 防重复两层：Python 侧 `set` 去重 + 数据库侧 `uniq_houseinfo` 联合唯一索引（8 个业务字段，`Non_unique=0`）

## Lab 3 提交内容

```text
lab_scrapy/
├── scrapydemo/                    Scrapy 项目源代码
│   ├── scrapy.cfg
│   └── scrapydemo/
│       ├── items.py               Item 定义（content / author / tags）
│       ├── settings.py            关键配置（ROBOTSTXT_OBEY=False / UA / LOG_LEVEL）
│       ├── middlewares.py
│       ├── pipelines.py
│       └── spiders/
│           └── quote.py           解析函数 parse() + 翻页逻辑（li.next a）
├── check.py                       数据校验脚本（条数 / 空值 / CSV 导出）
├── REPORT.md                      实验报告
├── data/
│   ├── quotes.json                100 条名言（Scrapy 原生 JSON 输出）
│   └── quotes.csv                 100 条名言（UTF-8，带表头）
└── images/
    ├── 01_items_py.png            Item 字段定义（含行号）
    ├── 02_settings_py.png         关键配置项（含行号）
    ├── 03_quote_py.png            解析函数与翻页代码（含行号）
    ├── 04_terminal_create.png     项目创建与 spider 生成过程
    ├── 05_terminal_run.png        爬取运行日志与统计指标
    ├── 06_validation.png          数据校验输出
    └── 07_pagination.png          翻页元素证据（第 1 页 vs 第 10 页）
```

### Lab 3 关键结果

- 数据来源：`https://quotes.toscrape.com/`（状态码 200，每页 10 条，共 10 页）
- **域名说明**：任务原写的 `quotes.toscrap.com` 已被抢注商占用（302 → hugedomains，403），
  改用 Scrapy 官方练习站 `quotes.toscrape.com`，页面结构与数据量与原题完全一致
- 翻页机制：`response.css("li.next a::attr(href)")` 取下一页地址 →
  `yield response.follow(next_page, callback=self.parse)` 递归；末页无 `li.next` 故自动终止
- 抓取结果：10 次请求 / 10 个响应 / **100 条 item** / 50 位作者 / 耗时 10.93 秒
- 队列自检：`scheduler/enqueued == dequeued == request_count == response_received_count == 10`
- 数据完整性：`content` / `author` 空值 **0** 条，CSV 导出 100 行

## 实验平台

- 平台：SmartPark DataLab（`https://115.159.159.82`）
- 环境：课程实验环境 Docker 容器 + JupyterLab
- 采集方式：`requests`（JSON API 分页）+ `BeautifulSoup`（静态 HTML 解析）
- 爬虫框架：Scrapy 2.19.0 / Python 3.12.3（课程容器内）
- 存储：MySQL 8.4.11（课程容器 `mysql:3306`，库 `smartpark_lab`）

## 说明

- `data/` 与 `images/` 均为实验真实产物，未使用任何示例或占位数据。
- 仓库内不含 `.env`、个人账号凭据或教师答案。
- 报告中的问答由本人使用自己的话改写；AI 辅助了代码骨架整理、截图裁切红框与文字组织，
  全部代码均在课程容器内逐单元格执行并核对结果。
