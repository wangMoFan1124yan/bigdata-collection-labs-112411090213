# -*- coding: utf-8 -*-
"""
实验二 · 第二阶段：安居客教学站房源采集与 CSV 存储
Lab 2 / Phase 2 - collect house listings and store them as CSV.

运行方式（课程 JupyterLab 内，容器路径 /home/pwuser/workspace/L02_reliable_collection）：
    python anjuke.py

产出：
    data/houseinfo.csv   UTF-8-SIG 编码，8 列，600 行数据（去重后）
"""

import csv
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------- 配置
BASE_URL = "http://www.bspider.top/anjuke/"

# 关键：必须伪装成完整浏览器 UA。短 UA（"Mozilla/5.0"）会被教学站的反爬
# 拦截，返回"访问验证"页而不是房源列表。
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

FIELDS = ["title", "house", "address", "struct", "area", "floor", "maketime", "price"]

DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "houseinfo.csv"

MAX_PAGES = 30      # 安全页数上限，防止无限循环
REQUEST_INTERVAL = 1.2   # 每次翻页至少等待 1 秒


# ---------------------------------------------------------------- 请求
def fetch(url, retries=5):
    """请求页面并返回解析好的 soup。失败时重试，超过次数抛出异常。"""
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=60)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            # 反爬验证页的 CSS 路径里含 "Antispam"，用 ASCII 判断不受编码影响
            if "Antispam" in r.text:
                raise RuntimeError("返回的是访问验证页，不是房源列表")
            return BeautifulSoup(r.text, "html.parser")
        except Exception as exc:
            last_error = exc
            print(f"    请求失败（第 {attempt}/{retries} 次）：{exc}")
            time.sleep(3)
    raise RuntimeError(f"无法获取页面：{url}，最后一次错误：{last_error}")


# ---------------------------------------------------------------- 解析
def parse_row(row):
    """把一条房源容器解析成 dict，字段顺序与 FIELDS 一致。"""
    # 属性区：div.property-content-info（排除楼栋信息的那个 div）
    info = row.select_one("div.property-content-info:not(.property-content-info-comm)")
    items = info.select("p") if info else []

    def item_text(index):
        """按下标取属性项；越界或缺失时返回空字符串。"""
        if 0 <= index < len(items):
            return items[index].get_text(strip=True)
        return ""

    # 户型在带 attribute class 的 p 里，单独取，避免靠下标硬猜
    struct_node = row.select_one("p.property-content-info-attribute")
    struct = struct_node.get_text(strip=True) if struct_node else ""

    # 建造年代：按"年建造"特征找，找不到留空
    maketime = ""
    for item in items:
        text = item.get_text(strip=True)
        if "年建造" in text:
            maketime = text
            break

    # 面积：属性区第 2 项（带面积单位）
    area = ""
    for item in items:
        text = item.get_text(strip=True)
        if "㎡" in text or "平米" in text:
            area = text
            break

    # 楼层：属性区第 4 项；第 3 项是朝向（南北/东西），不能取错
    floor = item_text(3)

    # 单价：property-price-average 是每平方米单价；property-price-total 是总价
    price_node = row.select_one("p.property-price-average")
    price = price_node.get_text(strip=True) if price_node else ""

    # 地址：3 个 span 拼成完整地址，中间不额外插空格
    address_node = row.select_one("p.property-content-info-comm-address")
    if address_node:
        address = "".join(s.get_text(strip=True) for s in address_node.select("span"))
    else:
        address = ""

    house_node = row.select_one("p.property-content-info-comm-name")
    house = house_node.get_text(strip=True) if house_node else ""

    title_node = row.select_one("h3")
    title = title_node.get_text(strip=True) if title_node else ""

    return {
        "title": title,
        "house": house,
        "address": address,
        "struct": struct,
        "area": area,
        "floor": floor,
        "maketime": maketime,
        "price": price,
    }


# ---------------------------------------------------------------- 翻页
def next_page_url(soup, current_url):
    """返回下一页地址；已经是末页（下一页按钮被禁用）时返回 None。"""
    link = soup.select_one("a.next.next-active")
    if link is None:
        # 找不到可用的"下一页"按钮 -> 末页
        return None
    href = link.get("href")
    if not href:
        return None
    return urljoin(current_url, href)


def collect():
    """逐页采集，返回 (记录列表, 采集到的页数)。"""
    records = []
    visited = set()
    current_url = BASE_URL
    page_no = 0

    while True:
        page_no += 1
        if page_no > MAX_PAGES:
            raise RuntimeError(f"达到安全页数上限 {MAX_PAGES}，采集中止")

        if current_url in visited:
            raise RuntimeError(f"地址重复，疑似陷入循环：{current_url}")
        visited.add(current_url)

        print(f"[第 {page_no} 页] 请求 {current_url}")
        soup = fetch(current_url)

        rows = soup.select("div.property")
        if not rows:
            raise RuntimeError(f"第 {page_no} 页未解析到房源（div.property 为 0），采集中止")
        print(f"    本页 {len(rows)} 条，累计 {len(records) + len(rows)} 条")

        for row in rows:
            records.append(parse_row(row))

        nxt = next_page_url(soup, current_url)
        if nxt is None:
            print("    下一页按钮已禁用或消失 -> 到达末页")
            break
        if nxt in visited:
            raise RuntimeError(f"下一页地址已访问过，疑似重复：{nxt}")

        print(f"    下一页：{nxt}")
        time.sleep(REQUEST_INTERVAL)
        current_url = nxt

    return records, page_no


# ---------------------------------------------------------------- 去重 + 存 CSV
def save_csv(records):
    """按 8 个字段完全相同去重，写入 CSV，并回读校验。"""
    seen = set()
    unique = []
    for rec in records:
        key = tuple(rec[f] for f in FIELDS)
        if key in seen:
            continue
        seen.add(key)
        unique.append(rec)

    dup_count = len(records) - len(unique)
    print(f"去重前 {len(records)} 条，去掉完全相同记录 {dup_count} 条，剩余 {len(unique)} 条")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        writer.writerows([rec[f] for f in FIELDS] for rec in unique)

    # 回读校验（DictReader，表头不算数据行）
    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        print(f"回读表头：{reader.fieldnames}")
        print(f"回读数据行数：{len(rows)}")
        for idx, label in [(0, "第一条"), (len(rows) // 2, "中间一条"), (len(rows) - 1, "最后一条")]:
            print(f"  {label}：{rows[idx]}")

    return unique, dup_count, len(rows)


# ---------------------------------------------------------------- 主流程
def main():
    records, pages = collect()
    unique, dups, read_back = save_csv(records)

    print("\n===== 采集汇总 =====")
    print(f"成功采集页数：{pages}")
    print(f"采集记录数（去重前）：{len(records)}")
    print(f"完全相同的重复记录数：{dups}")
    print(f"CSV 数据行数：{read_back}")
    print(f"CSV 路径：{CSV_PATH.resolve()}")


if __name__ == "__main__":
    main()
