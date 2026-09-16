import os
import re
import requests

# SimplifyJobs 2026 / New Grad 岗位库 Raw 地址
URL = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/README.md"

# 专注 MLE / Data / SDE 相关的匹配关键词
KEYWORDS = [
    r"\bmle\b", r"machine learning", r"data scientist", r"data science",
    r"data analyst", r"applied scientist", r"\bsde\b", r"software engineer", 
    r"software development", r"quantitative"
]

def clean_text(text):
    """清理 Markdown 格式（如 **Bold**, [Text](url) 等）"""
    if not text:
        return ""
    # 提取 Markdown 链接中的纯文本 [Company](url) -> Company
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # 去除 HTML 标签如 <a ...>
    text = re.sub(r'<[^>]+>', '', text)
    # 去除 ** 或 *
    text = re.sub(r'[\*\`]', '', text)
    return text.strip()

def extract_link(cell):
    """从单元格提取真实的申请 URL"""
    if not cell:
        return None
    # 匹配 href="URL"
    href_match = re.search(r'href=["\']([^"\']+)["\']', cell)
    if href_match:
        return href_match.group(1)
    # 匹配 Markdown [apply](URL)
    md_match = re.search(r'\((https?://[^\)]+)\)', cell)
    if md_match:
        return md_match.group(1)
    return None

def fetch_and_filter():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    response = requests.get(URL, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch data. HTTP Status: {response.status_code}")
        return
    
    lines = response.text.split("\n")
    matched_jobs = []
    
    for line in lines:
        # 表格行必须包含 '|'
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            # 表格列通常为: | Company | Role | Location | Application | Age/Date | ...
            if len(parts) >= 5:
                company_raw = parts[1]
                role_raw = parts[2]
                location_raw = parts[3]
                link_raw = parts[4]
                
                # 排除表头行
                if "company" in company_raw.lower() or "---" in company_raw:
                    continue
                
                # 提取链接（如果没有有效链接或已关闭🔒，跳过）
                link = extract_link(link_raw)
                if not link or "🔒" in link_raw:
                    continue
                
                company = clean_text(company_raw)
                role = clean_text(role_raw)
                location = clean_text(location_raw)
                
                # 结合 company 和 role 进行关键词校验
                search_target = f"{company} {role}".lower()
                if any(re.search(kw, search_target) for kw in KEYWORDS):
                    matched_jobs.append(f"• **{company}** | {role}\n  📍 {location}\n  🔗 {link}")

    print(f"✅ Total matching New Grad jobs found: {len(matched_jobs)}")
    
    if matched_jobs:
        # 取最新的 10 个匹配岗位推送
        msg = "🎓 **New Grad (MLE / Data / SDE) 岗位推送**\n\n" + "\n\n".join(matched_jobs[:10])
        send_telegram(msg)
    else:
        print("⚠️ No matching jobs found.")

def send_telegram(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ Error: Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID in environment secrets.")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    res = requests.post(url, json=payload)
    print("Telegram API Response Code:", res.status_code)
    if res.status_code != 200:
        print("Telegram API Response Text:", res.text)

if __name__ == "__main__":
    fetch_and_filter()
