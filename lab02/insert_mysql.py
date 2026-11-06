# -*- coding: utf-8 -*-
"""
实验二 · 第三阶段：把第二阶段的 CSV 写入 MySQL 的 houseinfo 表

设计要点：
1. 只读 CSV，不重新采集 —— 采集与入库解耦，两个阶段互不影响。
2. 批量插入用 executemany()，而不是循环里逐条 execute()：
   498 条数据逐条插入要 498 次网络往返，批量后只需一次。
3. 防重复插入做了两层保险：
   - 第一层（Python 侧）：入库前先 SELECT 出数据库里已有的 8 字段组合，
     在内存里过滤掉已存在的记录，重复数据根本不会被送进数据库。
   - 第二层（数据库侧）：给 8 个业务字段建联合唯一索引，
     并用 INSERT ... ON DUPLICATE KEY UPDATE，即使第一层被绕过，
     数据库也不会出现两条完全相同的记录。
4. 事务：try 里 commit()，except 里 rollback()。
   中途出错时整批回滚，不会留下"插了一半"的脏数据。
5. id 是 AUTO_INCREMENT 主键，插入时不能指定，交给数据库自增。
"""

import csv
import sys
from pathlib import Path

import pymysql

# ---------------------------------------------------------------- 配置

DB_CONFIG = {
    "host": "mysql",
    "port": 3306,
    "user": "student",
    "password": "123456",
    "database": "smartpark_lab",
    "charset": "utf8mb4",
    "autocommit": False,        # 手动提交，事务可控
}

CSV_PATH = Path("data/houseinfo.csv")

# 8 个业务字段，顺序必须与 CSV 表头、parse_row() 返回字典的键顺序完全一致
FIELDS = ["title", "house", "address", "struct", "area", "floor", "maketime", "price"]

# 联合唯一索引覆盖的全部列 —— 与 FIELDS 一一对应
UNIQUE_COLUMNS = FIELDS


# ---------------------------------------------------------------- 建索引

def ensure_unique_index(conn):
    """确保 8 个业务字段上有联合唯一索引。

    MySQL 没有 CREATE UNIQUE INDEX IF NOT EXISTS，
    所以先查 information_schema 判断，再决定要不要建。
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM information_schema.STATISTICS
            WHERE table_schema = %s AND table_name = 'houseinfo'
              AND index_name = 'uniq_houseinfo'
            """,
            (DB_CONFIG["database"],),
        )
        exists = cur.fetchone()[0]

        if exists:
            print("[索引] uniq_houseinfo 已存在，跳过创建")
            return

        cols = ", ".join(f"`{c}`" for c in UNIQUE_COLUMNS)
        cur.execute(f"CREATE UNIQUE INDEX uniq_houseinfo ON houseinfo ({cols})")
        conn.commit()
        print(f"[索引] 已创建联合唯一索引 uniq_houseinfo ({cols})")


# ---------------------------------------------------------------- 读 CSV

def read_csv(path):
    """读取 CSV，返回 (记录列表, 表头)。

    utf-8-sig：带 BOM，Excel 直接打开不乱码
    newline=""：交给 csv 模块自己处理换行，不能用默认的 universal newlines
    """
    if not path.exists():
        raise FileNotFoundError(f"找不到 CSV 文件：{path}")

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        rows = list(reader)

    if header != FIELDS:
        raise ValueError(
            f"CSV 表头与预期不一致。\n  实际：{header}\n  预期：{FIELDS}"
        )

    print(f"[读取] {path} 共 {len(rows)} 条数据，表头校验通过")
    return rows, header


# ---------------------------------------------------------------- 主流程

def main():
    conn = None
    cur = None
    try:
        # ---------- 连接 ----------
        conn = pymysql.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("[连接] 已连接 MySQL：%s / %s" % (DB_CONFIG["host"], DB_CONFIG["database"]))

        # ---------- 建唯一索引（防重复的第二层保险）----------
        ensure_unique_index(conn)

        # ---------- 入库前条数 ----------
        cur.execute("SELECT COUNT(*) FROM houseinfo")
        count_before = cur.fetchone()[0]
        print(f"[入库前] houseinfo 现有条数 = {count_before}")

        # ---------- 读 CSV ----------
        rows, _ = read_csv(CSV_PATH)

        # ---------- 第一层保险：查已有记录，在 Python 侧过滤 ----------
        # 把数据库里现有的 8 字段组合读出来，组成一个 set
        select_cols = ", ".join(f"`{c}`" for c in FIELDS)
        cur.execute(f"SELECT {select_cols} FROM houseinfo")
        existing = {tuple(r) for r in cur.fetchall()}
        print(f"[查重] 数据库中已有 {len(existing)} 组不重复的记录")

        # 只保留数据库里不存在的记录
        to_insert = []
        skipped = 0
        for row in rows:
            key = tuple(row[f] for f in FIELDS)
            if key in existing:
                skipped += 1
                continue
            existing.add(key)      # 同时防止 CSV 内部自身重复
            to_insert.append(key)

        print(f"[查重] CSV {len(rows)} 条中，已存在 {skipped} 条，本次需新增 {len(to_insert)} 条")

        # ---------- 批量插入 ----------
        # 第二层保险：ON DUPLICATE KEY UPDATE 让重复变成无害操作
        placeholders = ", ".join(["%s"] * len(FIELDS))
        insert_sql = (
            f"INSERT INTO houseinfo ({select_cols}) VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE "
            + ", ".join(f"`{c}` = VALUES(`{c}`)" for c in FIELDS)
        )

        if to_insert:
            cur.executemany(insert_sql, to_insert)
            conn.commit()           # 全部成功才提交
            print(f"[插入] executemany 批量插入 {len(to_insert)} 条，已 commit()")
        else:
            print("[插入] 没有需要新增的记录，跳过插入")

        # ---------- 入库后条数 ----------
        cur.execute("SELECT COUNT(*) FROM houseinfo")
        count_after = cur.fetchone()[0]
        added = count_after - count_before
        print(f"[入库后] houseinfo 现有条数 = {count_after}，本次新增 = {added}")

        # ---------- 抽样展示 ----------
        print("\n[抽样] 前 3 条：")
        cur.execute(
            f"SELECT id, {select_cols} FROM houseinfo ORDER BY id LIMIT 3"
        )
        for r in cur.fetchall():
            print("   ", r)

        print("\n[完成] 入库流程正常结束")

    except Exception as exc:
        # 出错：整批回滚，不留半截数据
        if conn is not None:
            conn.rollback()
            print(f"[错误] {type(exc).__name__}: {exc}")
            print("[回滚] 已执行 rollback()，本次插入全部撤销")
        sys.exit(1)
    finally:
        # 无论成功失败，都把游标和连接关掉
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
        print("[清理] 游标与连接已关闭")


if __name__ == "__main__":
    main()
