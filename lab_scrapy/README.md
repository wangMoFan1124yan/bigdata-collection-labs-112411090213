# Scrapy 翻页采集（quotes.toscrape.com）

- 姓名：王莫凡
- 学号：112411090213
- 班级：数据1241

## 目录

```text
lab_scrapy/
├── scrapydemo/       Scrapy 项目源代码（items.py / settings.py / spiders/quote.py）
├── check.py          数据校验脚本
├── REPORT.md         实验报告
├── data/             quotes.json（100 条）+ quotes.csv（100 条）
└── images/           7 张实验过程截图
```

## 快速复现

```bash
cd scrapydemo
scrapy crawl quote -o quotes.json
python3 ../check.py
```

## 说明

题目原域名 `quotes.toscrap.com` 已被抢注商占用（302 → hugedomains，403），
改用 Scrapy 官方练习站 `quotes.toscrape.com`，页面结构与数据量与原题一致。
详见 `REPORT.md` 开头说明。
