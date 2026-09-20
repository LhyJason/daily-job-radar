import os
import time
import html
import requests

# SimplifyJobs 现在维护的机器可读数据源（README 从不被解析，用这个 JSON）
LISTINGS_URL = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json"

# 可浏览的完整岗位表格（早于时间窗口的岗位在这里自己翻）
BROWSE_URL = "https://github.com/SimplifyJobs/New-Grad-Positions"

# 只要这些分类：SDE / DS / AI / MLE
TARGET_CATEGORIES = {"Software", "AI/ML/Data"}

# 只推近多少小时内新发布的岗位
WINDOW_HOURS = 72

# 单条消息最多展示多少条（防止 Telegram 消息过长）
MAX_JOBS = 15

# 如果只想要美国/加拿大/Remote 的岗位，把下面设为 True
US_CANADA_REMOTE_ONLY = False


def fetch_and_filter():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        res = requests.get(LISTINGS_URL, headers=headers, timeout=20)
    except Exception as e:
        print(f"Error fetching listings: {e}")
        send_telegram("🤖 <b>Job Radar</b>\n\n抓取失败：无法连接数据源。")
        return

    if res.status_code != 200:
        print(f"⚠️ Failed to fetch listings, status code: {res.status_code}")
        send_telegram(f"🤖 <b>Job Radar</b>\n\n抓取失败，HTTP {res.status_code}。")
        return

    try:
        listings = res.json()
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        send_telegram("🤖 <b>Job Radar</b>\n\n数据源解析失败（不是合法 JSON）。")
        return

    cutoff = time.time() - WINDOW_HOURS * 3600

    jobs = []
    for job in listings:
        # 只要还开着、可见、且属于目标分类的岗位
        if not job.get("active"):
            continue
        if not job.get("is_visible"):
            continue
        if job.get("category") not in TARGET_CATEGORIES:
            continue

        # 只保留近 WINDOW_HOURS 小时内发布的
        if job.get("date_posted", 0) < cutoff:
            continue

        locations = job.get("locations") or []
        if US_CANADA_REMOTE_ONLY and not _is_us_ca_remote(locations):
            continue

        jobs.append(job)

    # 按发布时间倒序，最新的在前
    jobs.sort(key=lambda j: j.get("date_posted", 0), reverse=True)

    total = len(jobs)
    print(f"✅ Matched (active, last {WINDOW_HOURS}h) jobs: {total}")

    matched = []
    for job in jobs[:MAX_JOBS]:
        company = html.escape(str(job.get("company_name", "")).strip())
        role = html.escape(str(job.get("title", "")).strip())
        location = html.escape(", ".join(job.get("locations") or []) or "N/A")
        link = job.get("url", "")

        matched.append(
            f"• <b>{company}</b> | {role}\n"
            f"  📍 {location}\n"
            f"  🔗 {link}"
        )

    if matched:
        header = f"🎓 <b>New Grad (SDE / DS / AI / MLE) · 近 {WINDOW_HOURS}h 新岗位</b>\n\n"
        msg = header + "\n\n".join(matched)
        if total > MAX_JOBS:
            msg += f"\n\n…还有 {total - MAX_JOBS} 条未展示。"
    else:
        msg = f"🤖 <b>Job Radar</b>\n\n近 {WINDOW_HOURS}h 内暂无符合条件的在招新岗位。"

    # 末尾附上完整列表链接，方便翻更早的
    msg += f"\n\n📚 <a href=\"{BROWSE_URL}\">查看完整列表（更早的岗位）</a>"

    send_telegram(msg)


def _is_us_ca_remote(locations):
    """粗略判断是否美国/加拿大/Remote。数据里 UK 岗位很多，需要时用来过滤。"""
    non_us = ("UK", "United Kingdom", "England")
    for loc in locations:
        if "remote" in loc.lower():
            return True
        if any(tag in loc for tag in non_us):
            continue
        # 其余默认当作美国/加拿大
        return True
    return False


def send_telegram(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("❌ Error: Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",  # HTML 比 legacy Markdown 稳，链接里的 _ * 不会炸
        "disable_web_page_preview": True,
    }

    r = requests.post(url, json=payload)
    print(f"Telegram API Status Code: {r.status_code}")
    if r.status_code != 200:
        print(f"Error detail: {r.text}")


if __name__ == "__main__":
    fetch_and_filter()
