import os
import re
import requests

# SimplifyJobs 官方最新的 New Grad 岗位列表文件
RAW_URL = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/README.md"

KEYWORDS = [
    r"\bmle\b", r"machine learning", r"data scientist", r"data science",
    r"data analyst", r"applied scientist", r"\bsde\b", r"software engineer", 
    r"software development", r"quant", r"developer"
]

def clean_text(text):
    if not text:
        return ""
    # 清理 Markdown 链接语法 [Text](url) -> Text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # 清理 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)
    # 清理表情符号或加粗符号
    text = re.sub(r'[\*\`🔥]', '', text)
    return " ".join(text.split())

def extract_link(cell):
    if not cell:
        return None
    # 提取 href="URL"
    href = re.search(r'href=["\'](https?://[^"\']+)["\']', cell)
    if href:
        return href.group(1)
    # 提取 Markdown (URL)
    md = re.search(r'\((https?://[^\)]+)\)', cell)
    if md:
        return md.group(1)
    return None

def fetch_and_filter():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        res = requests.get(RAW_URL, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"❌ Failed to fetch README, HTTP Status: {res.status_code}")
            return
    except Exception as e:
        print(f"❌ Network request error: {e}")
        return

    lines = res.text.split("\n")
    matched_jobs = []
    
    for line in lines:
        # 表格有效行过滤
        if "|" in line and not "---" in line and not "🔒" in line:
            parts = [p.strip() for p in line.split("|")]
            
            # 格式校验：| Company | Role | Location | Application Link/Age | ...
            if len(parts) >= 4:
                company_col = parts[1]
                role_col = parts[2]
                location_col = parts[3]
                
                # 跳过表头
                if "company" in company_col.lower() or "role" in role_col.lower():
                    continue

                company = clean_text(company_col)
                role = clean_text(role_col)
                location = clean_text(location_col)
                
                # 从整行提取投递链接
                link = extract_link(line)
                if not link:
                    continue

                # 匹配目标岗位关键词
                target_text = f"{company} {role}".lower()
                if any(re.search(kw, target_text) for kw in KEYWORDS):
                    matched_jobs.append(f"• **{company}** | {role}\n  📍 {location}\n  🔗 {link}")

    print(f"✅ Parsed total {len(matched_jobs)} matching jobs.")

    if matched_jobs:
        # 取最新前 8 条进行推送
        msg = "🎓 **New Grad (MLE / Data / SDE) 最新岗位推送**\n\n" + "\n\n".join(matched_jobs[:8])
        send_telegram(msg)
    else:
        print("⚠️ No matching jobs found.")

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
    print(f"Telegram Push Status: {r.status_code}")
    if r.status_code != 200:
        print(f"Error Response: {r.text}")

if __name__ == "__main__":
    fetch_and_filter()
