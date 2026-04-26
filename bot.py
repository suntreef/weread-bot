import time, random, os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

LOG_FILE = '/app/data/run.log'

def log_msg(msg):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)

def send_push(token, title, content):
    if not token: return
    try:
        url = "http://www.pushplus.plus/send"
        data = {"token": token, "title": title, "content": content}
        requests.post(url, json=data, timeout=10)
        log_msg("📩 微信推送已发送！")
    except Exception as e:
        log_msg(f"⚠️ 推送失败: {e}")

def get_driver():
    # 核心修复 1：每次启动前，暴力清理可能残留的浏览器锁文件
    lock_file = '/app/data/chrome_profile/SingletonLock'
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            log_msg("🧹 已清理异常残留的浏览器锁文件...")
        except Exception as e:
            log_msg(f"⚠️ 清理锁文件失败: {e}")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # 核心修复 2：加回并强化 NAS 必备的无显卡渲染参数
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer") 
    
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-data-dir=/app/data/chrome_profile")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

def check_login_and_get_qr():
    log_msg("🔍 开始检测微信读书登录状态...")
    qr_path = '/app/data/qrcode.png'
    try:
        driver = get_driver()
        driver.get("https://weread.qq.com/web/shelf")
        time.sleep(5)
        
        if "扫码" in driver.page_source or "login" in driver.current_url:
            log_msg("⚠️ 未登录，正在截取二维码...")
            driver.save_screenshot(qr_path)
            log_msg("✅ 二维码已生成！请刷新网页扫码（60秒内）。")
            
            for _ in range(30):
                time.sleep(2)
                if "扫码" not in driver.page_source:
                    log_msg("🎉 扫码成功！登录状态已保存。")
                    if os.path.exists(qr_path): os.remove(qr_path)
                    return
            log_msg("⌛ 扫码超时。")
        else:
            log_msg("✅ 当前已是登录状态。")
            if os.path.exists(qr_path): os.remove(qr_path)
    except Exception as e:
        log_msg(f"❌ 检测异常: {e}")
    finally:
        try: driver.quit()
        except: pass

def start_reading(book_url, reading_minutes, push_token=""):
    log_msg(f"🚀 启动阅读任务，目标: {reading_minutes} 分钟")
    
    try:
        driver = get_driver()
        
        if not book_url or book_url.strip() == "" or "xxxxxx" in book_url:
            log_msg("🤖 未配置指定书籍，尝试从书架自动选取...")
            driver.get("https://weread.qq.com/web/shelf")
            time.sleep(5)
            books = driver.find_elements(By.CSS_SELECTOR, "a[href^='/web/reader/']")
            if books:
                book_url = books[0].get_attribute('href')
                log_msg(f"📚 自动选取书籍成功，准备进入阅读...")
            else:
                msg = "❌ 书架为空或未登录，无法自动选书。"
                log_msg(msg)
                send_push(push_token, "阅读任务失败", msg)
                return

        driver.get(book_url)
        time.sleep(8)
        
        if "扫码" in driver.page_source or "login" in driver.current_url:
            msg = "⚠️ 账号登录失效，任务取消，请重新扫码。"
            log_msg(msg)
            send_push(push_token, "阅读登录失效", msg)
            return
        
        end_time = time.time() + (reading_minutes * 60)
        log_msg(f"📖 开始拟真阅读...")
        
        while time.time() < end_time:
            if random.random() < 0.8:
                driver.execute_script(f"window.scrollBy(0, {random.randint(300, 700)});")
            else:
                driver.execute_script(f"window.scrollBy(0, -{random.randint(100, 300)});")
                
            try:
                next_btn = driver.find_element(By.XPATH, "//*[contains(text(), '下一章')]")
                if next_btn.is_displayed():
                    driver.execute_script("arguments[0].click();", next_btn)
                    log_msg("翻页：进入下一章")
                    time.sleep(3)
            except: pass
            
            time.sleep(random.uniform(5.0, 15.0))
        
        msg = f"🏆 今日 {reading_minutes} 分钟阅读任务圆满完成！"
        log_msg(msg)
        send_push(push_token, "微信读书打卡成功", msg)
        
    except Exception as e:
        msg = f"❌ 运行异常: {e}"
        log_msg(msg)
        send_push(push_token, "阅读任务异常", msg)
    finally:
        try: driver.quit()
        except: pass
