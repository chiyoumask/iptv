# File: tv.py
# 解析 YouTube 直播流并合并国内静态源，生成 IPTV 播放列表。
# 本地或 GitHub Actions 中均可运行。
import subprocess
import datetime
import os
import sys
import time

# 你的頻道列表（名稱, YouTube live URL）
channels = [
    ("TVBS新聞", "https://www.youtube.com/watch?v=m_dhMSvUCIc"),
    ("東森新聞", "https://www.youtube.com/watch?v=V1p33hqPrUk"),
    ("民視新聞", "https://www.youtube.com/watch?v=ylYJSBUgaMA"),
    ("台視新聞", "https://www.youtube.com/watch?v=MaTO_CAzqJA"),
    ("中視新聞", "https://www.youtube.com/watch?v=baDV1O5EBP0"),
    ("三立新聞", "https://www.youtube.com/watch?v=N2TUvJ13Oxg"),
    ("中天新聞", "https://www.youtube.com/watch?v=vr3XyVCR4T0"),
    ("華視新聞", "https://www.youtube.com/watch?v=wM0g8EoUZ_E"),
    ("寰宇新聞", "https://www.youtube.com/watch?v=6IquAgfvYmc"),
    ("寰宇台灣", "https://www.youtube.com/watch?v=w87VGpgd90U"),
    ("三立財經", "https://www.youtube.com/watch?v=pF507BLtbqU"),
    ("東森財經", "https://www.youtube.com/watch?v=1I2iq41Akmo"),
    ("非凡財經", "https://www.youtube.com/watch?v=eA6Aczd3FZM"),
    ("寰宇財經", "https://www.youtube.com/watch?v=yAUQQ0DhPxI"),
]

output_file = "IPTV.m3u"
# 国内静态源（央视/卫视/重庆），地址固定、不随定时任务更新。
# 维护方式：直接改这个文件并推送，下次运行时会自动合并进 IPTV.m3u。
static_file = "channels_static.m3u"

# 重试次数：先尝试 web 客户端，失败后切换 android 客户端绕过封锁
retry_clients = ["web", "android"]
max_retries = len(retry_clients)


def _clean_stderr(stderr):
    """过滤掉无用的 WARNING 行，只保留 ERROR 等关键信息，便于排错。"""
    lines = [
        ln for ln in stderr.splitlines()
        if ln.strip() and not ln.startswith("WARNING")
    ]
    return "\n".join(lines).strip()


def get_m3u8_url(youtube_url):
    """带重试与客户端切换的解析。返回 m3u8 URL 或 None。"""
    for attempt, client in enumerate(retry_clients):
        try:
            cmd = [
                "yt-dlp",
                "-f", "b",  # 用 b 而非 best，抑制 "pre-merged format" 的 WARNING
                "-g",
                "--no-playlist",
                "--extractor-args", f"youtube:player_client={client}",
                youtube_url,
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )
            # yt-dlp -g 成功时把流地址打到 stdout；优先以 stdout 有无 http 链接为准
            url = next(
                (u for u in result.stdout.splitlines() if u.strip().startswith("http")),
                None,
            )
            if url:
                return url
            err = _clean_stderr(result.stderr)
            print(f"  尝试 {attempt + 1}/{max_retries} (client={client}) 失败: {err[:200]}")
        except subprocess.TimeoutExpired:
            print(f"  尝试 {attempt + 1}/{max_retries} (client={client}) 超时")
        except Exception as e:
            print(f"  尝试 {attempt + 1}/{max_retries} (client={client}) 例外: {e}")
        # 指数退避
        if attempt < max_retries - 1:
            time.sleep(3 * (attempt + 1))
    return None


def load_last_successful_urls(path):
    """解析现有 IPTV.m3u，只返回台湾频道的历史地址字典。

    关键：必须只认 group-title="台湾" 的频道，否则会把国内 rtsp 静态地址
    误当作台湾历史地址沿用（地址类型完全不同，且国内源不应被脚本管理）。
    """
    last_urls = {}
    if not os.path.exists(path):
        return last_urls
    current_name = None
    is_taiwan = False
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#EXTINF"):
                    # 判断是否属于台湾分组
                    is_taiwan = 'group-title="台湾"' in line
                    # 取逗号后的频道显示名
                    if "," in line:
                        current_name = line.split(",", 1)[1].strip()
                    else:
                        current_name = None
                elif line.startswith("http") and current_name and is_taiwan:
                    last_urls[current_name] = line
                    current_name = None
                    is_taiwan = False
                else:
                    current_name = None
                    is_taiwan = False
    except Exception as e:
        print(f"读取上次结果失败（将忽略旧地址）: {e}")
    return last_urls


def load_static_part(path):
    """读取国内静态源文件全文（去首尾空白）。文件不存在返回空串并告警。"""
    if not os.path.exists(path):
        print(f"警告: 静态源文件 {path} 不存在，输出将只含台湾动态部分。")
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"读取静态源失败（将忽略）: {e}")
        return ""


def main():
    # 历史地址只从台湾部分读，避免误用国内静态地址
    last_urls = load_last_successful_urls(output_file)
    if last_urls:
        print(f"从上次结果中读到 {len(last_urls)} 个台湾频道的历史地址，失败时将沿用。\n")

    static_part = load_static_part(static_file)

    success, reused, skipped = 0, 0, 0
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(output_file, "w", encoding="utf-8") as f:
        # 头部
        f.write("#EXTM3U\n")
        f.write(f"# 更新時間: {now}\n\n")

        # 国内静态部分在前（央视/卫视/重庆）
        if static_part:
            f.write(static_part)
            f.write("\n\n")

        # 台湾动态部分在后
        for name, url in channels:
            print(f"解析: {name}")
            m3u8 = get_m3u8_url(url)
            if m3u8:
                f.write(f'#EXTINF:-1 tvg-name="{name}" group-title="台湾",{name}\n')
                f.write(f"{m3u8}\n")
                print(f"  ✓ 成功（新地址）\n")
                success += 1
            elif name in last_urls:
                f.write(f'#EXTINF:-1 tvg-name="{name}" group-title="台湾",{name}\n')
                f.write(f"{last_urls[name]}\n")
                print(f"  ↻ 解析失败，沿用上次成功地址\n")
                reused += 1
            else:
                print(f"  ✗ 失败且无历史地址，跳过该频道\n")
                skipped += 1

    # 总结
    total = len(channels)
    print(f"台湾频道: 成功 {success}，沿用旧地址 {reused}，跳过 {skipped}，共 {total}")
    if success + reused == 0:
        print("警告: 所有台湾频道均不可用，台湾部分将为空！")
        sys.exit(1)
    print(f"已生成: {os.path.abspath(output_file)}")


if __name__ == "__main__":
    main()
