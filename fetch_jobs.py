import os
import re
import requests

# SimplifyJobs 岗位 Raw 地址
URL = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/README.md"

# 覆盖 MLE、Data Science/Analyst、SDE 及 Quant 核心关键词
KEYWORDS = [
    r"\bmle\b", r"machine learning", r"data scientist", r"data science",
    r"data analyst", r"applied scientist", r"\bsde\b", r"software engineer", 
    r"software development", r"quant", r"developer"
]

def clean_html(text):
    if not text:
        return ""
    # 去除 HTML 标签与 Markdown 加粗
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'[\*\`]', '', text)
    return " ".join(text.split())

def extract_link(line):
    # 优先匹配 href="URL"
    href = re.search(r'href=["\'](https?://[^"\']+)["\']', line)
    if href:
        return href.group(1)
    # 备用匹配 Markdown (URL)
    md = re.search(r'\((https?://[^\)]+)\)', line)
    if md:
        return md.group(1)
    return None

def fetch_and_filter():
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(URL, headers=headers)
    
    if res.status_code != 200:
        print(f"❌ HTTP Error: {res.status_code}")
        return
        
    lines = res.text.split("\n")
    matched_jobs = []
    
    for line in lines:
        # 跳过表头、分隔线及已锁定的岗位
        if "|" not in line or "---" in line or "🔒" in line:
            continue
            
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 4:
            company = clean_html(parts[1])
            role = clean_html(parts[2])
            location = clean_html(parts[3]) if len(parts) > 3 else "USA"
            
            # 过滤无效数据行
            if not company or "company" in company.lower():
                continue

            link = extract_link(line)
            if not link:
                continue

            target_text = f"{company} {role}".lower()
            if any(re.search(kw, target_text) for kw in KEYWORDS):
                matched_jobs.append(f"• **{company}** | {role}\n  📍 {location}\n  🔗 {link}")

    print(f"✅ Found {len(matched_jobs)} matching New Grad jobs.")

    if matched_jobs:
        # 挑选前 8 条推送，防止单条消息文本过长
        msg = "🎓 **New Grad (MLE / Data / SDE) 岗位推送**\n\n" + "\n\n".join(matched_jobs[:8])
        send_telegram(msg)
    else:
        print("⚠️ No matching jobs found.")

def send_telegram(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ Missing Secrets: TELEGRAM_TOKEN or TELEGRAM_CHAT_ID")
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
        print(f"API Error Response: {r.text}")

if __name__ == "__main__":
    fetch_and_filter()
