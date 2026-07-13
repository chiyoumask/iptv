# IPTV 直播源（国内静态 + 台湾动态）

通过 GitHub Actions 每 6 小时自动解析 YouTube 直播流，与国内静态源合并，生成统一的 `IPTV.m3u`，供 IPTV 播放器订阅。

## 播放列表构成

最终的 `IPTV.m3u` 由两部分拼接而成：

1. **国内静态部分**（央视 / 卫视 / 重庆三个分组）：地址固定，来自 `channels_static.m3u`，**不随定时任务更新**。
2. **台湾动态部分**（15 个台湾新闻/财经频道）：由 `tv.py` 用 yt-dlp 解析 YouTube 直播流得到，每 6 小时刷新。频道包括 TVBS、东森、民视、台视、中视、三立、中天、华视、寰宇新闻、寰宇台湾、三立财经、东森财经、非凡财经、寰宇财经、TVB财经。

输出顺序：央视 → 卫视 → 重庆 → 台湾。

## 订阅地址

将下面的 `<用户名>` 和 `<仓库名>` 替换为你的实际信息（仓库需为**公开**），粘贴到 IPTV 播放器的「添加播放列表 / 订阅链接」中即可：

```
https://raw.githubusercontent.com/<用户名>/<仓库名>/main/IPTV.m3u
```

> 公开仓库的 raw 链接可被大多数播放器（IPTV Smarters、TiviMate、PotPlayer、VLC 等）直接读取。

## 工作原理

```
cron 每 6 小时（或手动触发）
  → GitHub Actions runner 拉取仓库
  → 安装 yt-dlp
  → python tv.py 解析台湾频道 YouTube 直播流
  → 合并 channels_static.m3u（国内）+ 台湾动态源 → 生成 IPTV.m3u
  → 提交回仓库
  → 播放器通过 raw 链接读取最新列表
```

**容错机制**：台湾某频道某次解析失败时，自动沿用上一次成功的地址；既无新地址又无历史地址才跳过。国内静态部分每次原样保留，不受解析成败影响。

## 如何维护国内（央视/卫视/重庆）频道

国内源的地址是固定的、不需要定时更新，所以**不归脚本管理**，直接维护文件即可：

1. 编辑仓库根目录的 `channels_static.m3u`（增删频道或改地址，保持 `#EXTINF` + 地址的标准 m3u 格式）。
2. 提交并推送到 GitHub。
3. 下一次定时任务（或手动触发 Actions）运行时，会自动把新的 `channels_static.m3u` 合并进 `IPTV.m3u`。

> 注意：`channels_static.m3u` **不要写 `#EXTM3U` 头**，这个头由最终输出的 `IPTV.m3u` 承担，避免重复。

## 本地运行

```bash
pip install -r requirements.txt
python tv.py
```

运行后在当前目录生成 `IPTV.m3u`（读取同目录的 `channels_static.m3u` 合并）。

## 目录结构

```
.
├── .github/workflows/update-iptv.yml  # GitHub Actions 定时任务
├── tv.py                              # 解析脚本（台湾动态源）
├── channels_static.m3u                # 国内静态源（手动维护）
├── requirements.txt                   # Python 依赖
├── IPTV.m3u                           # 最终生成的播放列表（自动产出）
└── README.md
```

## ⚠️ 关于 YouTube 封锁

GitHub Actions runner 使用的是 Azure 数据中心 IP，YouTube 可能对这些 IP 段做风控。本项目的缓解措施：

1. 每次解析带 2 次重试，并切换 yt-dlp 的 `web`/`android` 客户端尝试绕过。
2. 台湾频道失败沿用上次成功地址，台湾部分不会变成空文件。
3. 国内静态部分完全不依赖 YouTube，始终保持可用。

若台湾部分长期大面积失败，可考虑接入代理或改用海外 VPS 运行（届时国内静态源的合并逻辑保持不变）。
