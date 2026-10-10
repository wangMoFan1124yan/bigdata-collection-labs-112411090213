# 大数据采集与处理实验

- 姓名：王莫凡
- 学号：112411090213
- 班级：数据1241

## 实验目录

| 实验 | 内容 | 目录 |
|---|---|---|
| Lab 1 | 静态页面与 API 数据采集 | [`lab01/`](lab01/) |

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

## 实验平台

- 平台：SmartPark DataLab（`https://115.159.159.82`）
- 环境：课程实验环境 Docker 容器 + JupyterLab
- 采集方式：`requests`（JSON API 分页）+ `BeautifulSoup`（静态 HTML 解析）
