# IPTV 直播源（国内静态 + 台湾动态）

本地手动运行脚本解析 YouTube 直播流，与国内静态源合并，生成统一的 `IPTV.m3u`，一键提交推送到 GitHub 仓库供 IPTV 播放器订阅。

> ⚠️ **为什么改为本地解析**：曾尝试用 GitHub Actions 定时在云端解析，但 runner IP 被 YouTube 风控，云端始终解析不到台湾源。经多日实测确认行不通，故回退为本地解析 + 手动推送。Actions 的定时任务已停用，仅保留 `workflow_dispatch` 作为日后云端连通性的可选自检。

## 播放列表构成

最终的 `IPTV.m3u` 由两部分拼接而成：

1. **国内静态部分**（央视 / 卫视 / 重庆三个分组）：地址固定，来自 `channels_static.m3u`，**不随解析任务更新**。
2. **台湾动态部分**（15 个台湾新闻/财经频道）：由 `tv.py` 用 yt-dlp 解析 YouTube 直播流得到。频道包括 TVBS、东森、民视、台视、中视、三立、中天、华视、寰宇新闻、寰宇台湾、三立财经、东森财经、非凡财经、寰宇财经、TVB财经。

输出顺序：央视 → 卫视 → 重庆 → 台湾。

## 订阅地址

将下面的 `<用户名>` 和 `<仓库名>` 替换为你的实际信息（仓库需为**公开**），粘贴到 IPTV 播放器的「添加播放列表 / 订阅链接」中即可：

```
https://raw.githubusercontent.com/<用户名>/<仓库名>/main/IPTV.m3u
```

> 公开仓库的 raw 链接可被大多数播放器（IPTV Smarters、TiviMate、PotPlayer、VLC 等）直接读取。

## 使用方式（一键更新）

双击仓库根目录的 **`更新IPTV.bat`**，脚本会自动完成：

```
[1/5] 解析台湾频道 YouTube 直播流         python tv.py
[2/5] 同步远端（防止推送冲突）           git pull --rebase
[3/5] 暂存 IPTV.m3u                     git add IPTV.m3u
[4/5] 提交更改（带时间戳）               git commit -m "手动更新 IPTV 直播源 <时间>"
[5/5] 推送到远程仓库                     git push
```

任何一步失败都会提示原因并中止，不会污染仓库状态。若 `IPTV.m3u` 无变化则跳过提交推送。

**前置依赖**：
- Python 3 + yt-dlp（`pip install -r requirements.txt`）
- 系统能直接用 `git` 命令（已配置好推送凭据）

**手动方式**（不想用 BAT 时）：
```bash
pip install -r requirements.txt
python tv.py
git add IPTV.m3u
git commit -m "手动更新 IPTV 直播源 <日期>"
git push
```

## 工作原理

```
本地触发（双击 更新IPTV.bat 或 python tv.py）
  → python tv.py 解析台湾频道 YouTube 直播流
  → 合并 channels_static.m3u（国内）+ 台湾动态源 → 生成 IPTV.m3u
  → 脚本自动 git pull --rebase / add / commit / push
  → 播放器通过 raw 链接读取最新列表
```

**容错机制**：
- 台湾某频道某次解析失败时，自动沿用上一次成功的地址；既无新地址又无历史地址才跳过。
- 国内静态部分每次原样保留，不受解析成败影响。
- 脚本若检测到全部台湾频道均不可用（`sys.exit(1)`），BAT 会中止推送，避免把坏结果覆盖到仓库。

## 如何维护国内（央视/卫视/重庆）频道

国内源地址固定、不需随解析更新，**直接维护文件即可**：

1. 编辑仓库根目录的 `channels_static.m3u`（增删频道或改地址，保持 `#EXTINF` + 地址的标准 m3u 格式）。
2. 提交并推送到 GitHub。
3. 下次本地运行 `更新IPTV.bat`（或 `python tv.py`）时，会自动把新的 `channels_static.m3u` 合并进 `IPTV.m3u`。

> 注意：`channels_static.m3u` **不要写 `#EXTM3U` 头**，这个头由最终输出的 `IPTV.m3u` 承担，避免重复。

## 目录结构

```
.
├── .github/workflows/update-iptv.yml  # GitHub Actions（仅手动触发，作可选云端自检）
├── tv.py                              # 解析脚本（台湾动态源）
├── channels_static.m3u                # 国内静态源（手动维护）
├── 更新IPTV.bat                       # 一键脚本（解析+提交+推送）
├── requirements.txt                   # Python 依赖（yt-dlp）
├── IPTV.m3u                           # 最终生成的播放列表（自动产出）
└── README.md
```

## ⚠️ 关于 GitHub Actions

workflow 已降级为**只保留手动触发**（`workflow_dispatch`），并且**不再做 commit/push**——你在 GitHub Actions 页面点 `Run workflow` 跑出来的结果只会在日志里显示，不会覆盖你本地推送的有效结果。这一步只是留作日后云端连通性的可选自检（例如想确认 YouTube 是否解封了 GitHub IP）。

主流程请始终用本地的 `更新IPTV.bat`。
