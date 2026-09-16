import os
import re
import requests

# 抓取 SimplifyJobs New Grad 岗位库 Raw Markdown
URL = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/README.md"

# 精准匹配 MLE, Data, SDE 相关岗位关键词
KEYWORDS = [
    r"\bmle\b", r"machine learning", r"data scientist", r"data science", 
    r"data analyst", r"applied scientist", r"\bsde\b", r"software engineer", r"software"
]

def fetch_and_filter():
    response = requests.get(URL)
    if response.status_code != 200:
        print(f"Failed to fetch data: {response.status_code}")
        return
    
    lines = response.text.split("\n")
    matched_jobs = []
    
    for line in lines:
        # 解析 Markdown 表格行，并且排除已关闭的岗位（没有申请链接的）
        if "|" in line and "http" in line:
            line_lower = line.lower()
            if any(re.search(kw, line_lower) for kw in KEYWORDS):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 5:
                    company = parts[1]
                    role = parts[2]
                    location = parts[3]
                    
                    # 提取 <a> 标签链接或 Markdown 超链接
                    link_match = re.search(r'href="([^"]+)"', parts[4]) or re.search(r'\((https?://[^\)]+)\)', parts[4])
                    link = link_match.group(1) if link_match else "N/A"
                    
                    # 清理 Markdown 加粗/链接标记
                    company = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', company)
                    company = re.sub(r'[\*\`]', '', company)
                    role = re.sub(r'[\*\`]', '', role)
                    
                    if link != "N/A":
                        matched_jobs.append(f"• **{company}** | {role}\n  📍 {location}\n  🔗 {link}")

    if matched_jobs:
        # 挑选最新的 10 个过滤后的岗位进行推送
        msg = "🚀 **今日 MLE / Data / SDE 新岗推送**\n\n" + "\n\n".join(matched_jobs[:10])
        send_telegram(msg)
    else:
        print("No matching jobs found today.")

def send_telegram(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID in environment variables.")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": text, 
        "parse_mode": "Markdown", 
        "disable_web_page_preview": True
    }
    res = requests.post(url, json=payload)
    print("Telegram response:", res.status_code, res.text)

if __name__ == "__main__":
    fetch_and_filter()
