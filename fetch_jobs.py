import os
import re
import requests

# 1. 明确指向包含实际岗位表格的两个子 Markdown 文件
URLS = [
    "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/Software%20Engineering.md",
    "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/Data%20Science%2C%20AI%20%26%20Machine%20Learning.md"
]

# 2. 地点筛选：美国 (US, USA, 各州缩写) 以及 香港 (Hong Kong, HK)
LOC_KEYWORDS = [
    r"\busa?\b", r"\bunited states\b", r"\bhong kong\b", r"\bhk\b",
    r"\bca\b", r"\bny\b", r"\bwa\b", r"\btx\b", r"\bma\b", r"\bil\b", r"\bnc\b", r"\bnj\b", r"\bremote\b"
]

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[\*\`🔥]', '', text)
    return " ".join(text.split())

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
                continue
            
            lines = res.text.split("\n")
            for line in lines:
                # 过滤掉非表格行、表头分隔符以及已经关闭(🔒)的岗位
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

                        # 地点过滤：必须包含美国或香港
                        loc_lower = location.lower()
                        if not any(re.search(kw, loc_lower) for kw in LOC_KEYWORDS):
                            continue

                        link = extract_link(line)
                        if not link:
                            continue

                        matched_jobs.append(f"• **{company}** | {role}\n  📍 {location}\n  🔗 {link}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    print(f"✅ Parsed total {len(matched_jobs)} matching target jobs.")

    if matched_jobs:
        # 挑选最新的 8 条推送，防止单条 Telegram 文本溢出
        msg = "🎓 **New Grad (SDE / DS / AI / MLE) 最新岗位 (美/港)**\n\n" + "\n\n".join(matched_jobs[:8])
        send_telegram(msg)
    else:
        print("⚠️ No matching jobs found.")

def send_telegram(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("❌ Error: Secrets TELEGRAM_TOKEN or TELEGRAM_CHAT_ID missing!")
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
