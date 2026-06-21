# IPTV 台湾新闻直播源

通过 GitHub Actions 每 6 小时自动解析 YouTube 直播流，生成 `.m3u` 播放列表，供 IPTV 播放器订阅。

## 频道列表

包含 12 个台湾新闻/财经直播频道：TVBS、东森、民视、台视、中视、三立、中天、华视、寰宇新闻、寰宇台湾、三立财经、东森财经。

## 订阅地址

将下面的 `<用户名>` 和 `<仓库名>` 替换为你的实际信息（仓库需为**公开**），粘贴到 IPTV 播放器的「添加播放列表 / 订阅链接」中即可：

```
https://raw.githubusercontent.com/<用户名>/<仓库名>/main/IPTV3.m3u
```

> 公开仓库的 raw 链接可被大多数播放器（IPTV Smarters、TiviMate、PotPlayer、VLC 等）直接读取。

## 工作原理

```
cron 每 6 小时（或手动触发）
  → GitHub Actions runner 拉取仓库
  → 安装 yt-dlp
  → python tv.py 解析各频道 YouTube 直播流
  → 生成 IPTV3.m3u 并提交回仓库
  → 播放器通过 raw 链接读取最新列表
```

**容错机制**：某频道某次解析失败时，自动沿用上一次成功的地址；既无新地址又无历史地址才跳过，保证列表始终可用。

## 本地运行

```bash
pip install -r requirements.txt
python tv.py
```

运行后在当前目录生成 `IPTV3.m3u`。

## 目录结构

```
.
├── .github/workflows/update-iptv.yml  # GitHub Actions 定时任务
├── tv.py                              # 解析脚本
├── requirements.txt                   # Python 依赖
├── IPTV3.m3u                          # 生成的播放列表（自动产出）
└── README.md
```

## ⚠️ 关于 YouTube 封锁

GitHub Actions runner 使用的是 Azure 数据中心 IP，YouTube 可能对这些 IP 段做风控。本项目的缓解措施：

1. 每次解析带 2 次重试，并切换 yt-dlp 的 `android`/`web` 客户端尝试绕过。
2. 失败沿用上次成功地址，列表不会变成空文件。

若长期大面积失败，可考虑接入代理或改用海外 VPS 运行。
