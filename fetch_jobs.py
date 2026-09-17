import os
import re
import requests

# SimplifyJobs 包含实际岗位表格的 Markdown 文件
URLS = [
    "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/Software%20Engineering.md",
    "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/Data%20Science%2C%20AI%20%26%20Machine%20Learning.md"
]

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[\*\`🔥]', '', text)
    return " ".join(text.split())

def escape_markdown(text):
    if not text:
        return ""
    # 转义 Telegram Markdown 中的敏感字符
    for char in ['_', '*', '`', '[']:
        text = text.replace(char, f'\\{char}')
    return text

def extract_link(cell):
    if not cell:
        return None
    href = re.search(r'href=["\'](https?://[^"\']+)["\']', cell)
    if href:
        return href.group(1)
    md = re.search(r'\((https?://[^\)]+)\)', cell)
    if md:
        return md.group(1)
    return None

def fetch_and_filter():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    matched_jobs = []

    for url in URLS:
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code != 200:
                print(f"⚠️ Failed to fetch {url}, status code: {res.status_code}")
                continue
            
            lines = res.text.split("\n")
            for line in lines:
                # 过滤非表格行、表头分隔符以及已经关闭(🔒)的岗位
                if "|" in line and not "---" in line and not "🔒" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 4:
                        company_col = parts[1]
                        role_col = parts[2]
                        location_col = parts[3]

                        if "company" in company_col.lower() or "role" in role_col.lower():
                            continue

                        company = clean_text(company_col)
                        role = clean_text(role_col)
                        location = clean_text(location_col)

                        link = extract_link(line)
                        if not link:
                            continue

                        safe_company = escape_markdown(company)
                        safe_role = escape_markdown(role)
                        safe_location = escape_markdown(location)

                        matched_jobs.append(f"• **{safe_company}** | {safe_role}\n  📍 {safe_location}\n  🔗 {link}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    print(f"✅ Total matched jobs: {len(matched_jobs)}")

    if matched_jobs:
        msg = "🎓 **New Grad (SDE / DS / AI / MLE) 全球最新岗位**\n\n" + "\n\n".join(matched_jobs[:8])
    else:
        msg = "🤖 **Job Radar 通知**\n\n数据抓取成功，但当前源中暂无最新岗位。"

    send_telegram(msg)

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
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    r = requests.post(url, json=payload)
    print(f"Telegram API Status Code: {r.status_code}")
    if r.status_code != 200:
        print(f"Error detail: {r.text}")

if __name__ == "__main__":
    fetch_and_filter()
