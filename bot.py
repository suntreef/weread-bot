import time, random, os
import requests
from playwright.sync_api import sync_playwright

LOG_FILE = '/app/data/run.log'
PROFILE_DIR = '/app/data/playwright_profile'

def log_msg(msg):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)

def send_push(token, title, content):
    if not token: return
    try:
        requests.post("http://www.pushplus.plus/send", json={"token": token, "title": title, "content": content}, timeout=10)
        log_msg("📩 微信推送已发送！")
    except Exception as e:
        log_msg(f"⚠️ 推送失败: {e}")

def check_login_and_get_qr():
    log_msg("🔍 开始检测微信读书登录状态 (基于 Playwright 引擎)...")
    qr_path = '/app/data/qrcode.png'
    try:
        with sync_playwright() as p:
            # 启动浏览器并加载持久化配置（免扫码的核心）
            browser = p.chromium.launch_persistent_context(
                user_data_dir=PROFILE_DIR,
                headless=True,
                args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"]
            )
            page = browser.new_page()
            page.goto("https://weread.qq.com/web/shelf", timeout=30000)
            page.wait_for_timeout(5000)

            if "扫码" in page.content() or "login" in page.url:
                log_msg("⚠️ 未登录，正在截取二维码...")
                page.screenshot(path=qr_path)
                log_msg("✅ 二维码已生成！请刷新网页扫码（60秒内）。")
                
                for _ in range(30):
                    page.wait_for_timeout(2000)
                    if "扫码" not in page.content():
                        log_msg("🎉 扫码成功！登录状态已保存。")
                        if os.path.exists(qr_path): os.remove(qr_path)
                        break
                else:
                    log_msg("⌛ 扫码超时。")
            else:
                log_msg("✅ 当前已是登录状态。")
                if os.path.exists(qr_path): os.remove(qr_path)
            
            browser.close()
    except Exception as e:
        log_msg(f"❌ 检测异常: {e}")

def start_reading(book_url, reading_minutes, push_token=""):
    log_msg(f"🚀 启动阅读任务，目标: {reading_minutes} 分钟")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch_persistent_context(
                user_data_dir=PROFILE_DIR,
                headless=True,
                args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"]
            )
            page = browser.new_page()

            # 智能找书逻辑
            if not book_url or book_url.strip() == "" or "xxxxxx" in book_url:
                log_msg("🤖 尝试从书架自动选取书籍...")
                page.goto("https://weread.qq.com/web/shelf", timeout=30000)
                page.wait_for_timeout(5000)
                
                # 寻找书架上的第一本书
                books = page.query_selector_all("a[href^='/web/reader/']")
                if books:
                    href = books[0].get_attribute('href')
                    book_url = "https://weread.qq.com" + href if href.startswith('/') else href
                    log_msg(f"📚 自动选取书籍成功，准备阅读...")
                else:
                    msg = "❌ 书架为空或未登录，无法选书。"
                    log_msg(msg)
                    send_push(push_token, "任务失败", msg)
                    browser.close()
                    return

            page.goto(book_url, timeout=30000)
            page.wait_for_timeout(8000)

            if "扫码" in page.content() or "login" in page.url:
                msg = "⚠️ 账号登录失效，请重新获取二维码扫码。"
                log_msg(msg)
                send_push(push_token, "阅读登录失效", msg)
                browser.close()
                return

            end_time = time.time() + (reading_minutes * 60)
            log_msg(f"📖 开始拟真阅读 (底层物理鼠标滚动模拟)...")
            
            while time.time() < end_time:
                # Playwright 独家绝技：真实模拟物理鼠标滚轮，防封号利器
                if random.random() < 0.8:
                    page.mouse.wheel(0, random.randint(300, 700))
                else:
                    page.mouse.wheel(0, -random.randint(100, 300))
                    
                # 智能寻找并点击下一章
                next_btn = page.query_selector("text='下一章'")
                if next_btn and next_btn.is_visible():
                    next_btn.click()
                    log_msg("翻页：进入下一章")
                    page.wait_for_timeout(3000)
                
                page.wait_for_timeout(random.uniform(5000, 15000))
            
            msg = f"🏆 今日 {reading_minutes} 分钟阅读任务圆满完成！"
            log_msg(msg)
            send_push(push_token, "微信读书打卡成功", msg)
            browser.close()
            
    except Exception as e:
        msg = f"❌ 运行异常: {e}"
        log_msg(msg)
        send_push(push_token, "阅读任务异常", msg)
