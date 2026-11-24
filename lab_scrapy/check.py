# -*- coding: utf-8 -*-
import io
import json
import csv
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with io.open("quotes.json", encoding="utf-8") as f:
    data = json.load(f)

print("count =", len(data))
print("authors =", len(set(x["author"] for x in data)))
print("first content =", data[0]["content"][:70])
print("last author =", data[-1]["author"])
print("all have content/author =", all(x["content"] and x["author"] for x in data))

# 顺便导出 CSV
with io.open("quotes.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["content", "author", "tags"])
    for x in data:
        w.writerow([x["content"], x["author"], ", ".join(x["tags"])])
print("csv written =", len(data))
