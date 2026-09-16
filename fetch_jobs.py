import os
import re
import requests

# SimplifyJobs New Grad Positions
URL = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/README.md"

KEYWORDS = [
    r"\bmle\b", r"machine learning", r"data scientist", r"data science", 
    r"data analyst", r"applied scientist", r"\bsde\b", r"software engineer", 
    r"software development", r"quant"
]

def clean_text(text):
    if not text:
        return ""
    # 提取 HTML 链接中的文字或 Markdown 链接
    text = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'[\*\`]', '', text)
    return text.strip()

def extract_link(text):
    if not text:
        return None
    # 匹配 href="URL"
    href_match = re.search(r'href=["\']([^"\']+)["\']', text)
    if href_match:
        return href_match.group(1)
    # 匹配 Markdown (URL)
    md_match = re.search(r'\((https?://[^\)]+)\)', text)
    if md_match:
        return md_match.group(1)
    return None

def fetch_and_filter():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ HTTP Error: {response.status_code}")
        return
    
    lines = response.text.split("\n")
    matched_jobs = []
    
    for line in lines:
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            # 过滤掉非表格行
            if len(parts) >= 5:
                # 表格字段一般为：| Company | Role | Location | Application | Age/Date |
                company_col = parts[1]
                role_col = parts[2]
                location_col = parts[3]
                app_col = parts[4]
                
                if "company" in company_col.lower() or "---" in company_col:
                    continue
                
                # 检查岗位是否锁定 (🔒 代表 closed)
                if "🔒" in app_col or "🔒" in line:
                    continue
                
                link = extract_link(app_col)
                if not link:
                    link = extract_link(line) # 全行备用提取
                
                if not link:
                    continue

                company = clean_text(company_col)
                role = clean_text(role_col)
                location = clean_text(location_col)
                
                target = f"{company} {role}".lower()
                if any(re.search(kw, target) for kw in KEYWORDS):
                    # Telegram 消息格式化
                    matched_jobs.append(f"• **{company}** | {role}\n  📍 {location}\n  🔗 {link}")

    print(f"✅ Found {len(matched_jobs)} matching New Grad jobs.")

    if matched_jobs:
        # 每次取前 8 条发送，防止 Telegram 超过 4096 字符上限限制
        msg = "🎓 **New Grad (MLE / Data / SDE) 最新岗位**\n\n" + "\n\n".join(matched_jobs[:8])
        send_telegram(msg)
    else:
        print("⚠️ No matching jobs found.")

def send_telegram(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ Missing Secrets!")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    res = requests.post(url, json=payload)
    print(f"Telegram Push Status Code: {res.status_code}")
    if res.status_code != 200:
        print(f"Response: {res.text}")

if __name__ == "__main__":
    fetch_and_filter()
