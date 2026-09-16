import os
import re
import requests

# SimplifyJobs 官方后端 API 接口 (包含最新 New Grad 增量岗位)
API_URL = "https://simplify.jobs/api/v2/jobs?jobTypes=Full%20Time&category=Software%20Engineering"

KEYWORDS = [
    r"\bmle\b", r"machine learning", r"data scientist", r"data science",
    r"data analyst", r"applied scientist", r"\bsde\b", r"software engineer", 
    r"software development", r"quant"
]

def fetch_and_filter():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    matched_jobs = []
    
    # 尝试从 Simplify API 获取最新岗位
    try:
        res = requests.get(API_URL, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            jobs = data.get("jobs", []) if isinstance(data, dict) else data
            for job in jobs:
                title = job.get("title", "")
                company = job.get("companyName", job.get("company", {}).get("name", "Unknown"))
                locations = ", ".join(job.get("locations", ["USA"]))
                url = job.get("url", job.get("applicationUrl", ""))
                
                target = f"{company} {title}".lower()
                if any(re.search(kw, target) for kw in KEYWORDS):
                    matched_jobs.append(f"• **{company}** | {title}\n  📍 {locations}\n  🔗 {url}")
    except Exception as e:
        print(f"API Fetch Warning: {e}")

    # 如果 API 没取到，使用备用开源镜像地址 (jobright/simplify-backup)
    if not matched_jobs:
        backup_url = "https://raw.githubusercontent.com/ SimplifyJobs/New-Grad-Positions/dev/README.md"
        try:
            raw_text = requests.get("https://raw.githubusercontent.com/jobright-ai/2026-Software-Engineer-New-Grad/main/README.md", headers=headers).text
            for line in raw_text.split("\n"):
                if "|" in line and "http" in line and not "---" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 4:
                        comp = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', parts[1])
                        role = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', parts[2])
                        link_m = re.search(r'\((https?://[^\)]+)\)', line) or re.search(r'href=["\']([^"\']+)["\']', line)
                        link = link_m.group(1) if link_m else ""
                        if link:
                            matched_jobs.append(f"• **{comp}** | {role}\n  🔗 {link}")
        except Exception as e:
            print(f"Backup Fetch Warning: {e}")

    print(f"✅ Total jobs parsed: {len(matched_jobs)}")

    # 组装推送消息
    if matched_jobs:
        msg = "🎓 **New Grad (MLE / Data / SDE) 岗位推送**\n\n" + "\n\n".join(matched_jobs[:8])
    else:
        # 兜底测试消息：验证 Telegram 通讯链
        msg = "🤖 **Job Radar 测试消息**\n\n系统运行正常，但今日目标源暂无增量岗位。Telegram 推送链路已通！"

    send_telegram(msg)

def send_telegram(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    print(f"Checking Secrets -> Token Exists: {bool(token)}, Chat ID Exists: {bool(chat_id)}")
    
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
    print(f"Telegram API Response Code: {r.status_code}")
    if r.status_code != 200:
        print(f"Telegram Error Detail: {r.text}")

if __name__ == "__main__":
    fetch_and_filter()
