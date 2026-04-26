import time, random, os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def start_reading(book_url, reading_minutes):
    print("启动浏览器...")
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-data-dir=/app/data/chrome_profile")
    
    driver = webdriver.Chrome(options=chrome_options)
    qr_path = '/app/data/qrcode.png'
    
    try:
        driver.get(book_url)
        driver.implicitly_wait(10)
        time.sleep(8) 
        
        if "扫码" in driver.page_source or "login" in driver.current_url:
            print("未登录，生成二维码...")
            driver.save_screenshot(qr_path)
            for _ in range(30): 
                time.sleep(2)
                if "扫码" not in driver.page_source:
                    print("扫码成功！")
                    if os.path.exists(qr_path): os.remove(qr_path)
                    break
            else:
                print("等待超时")
                return
                
        if os.path.exists(qr_path): os.remove(qr_path)

        end_time = time.time() + (reading_minutes * 60)
        print(f"开始阅读: {reading_minutes} 分钟")
        while time.time() < end_time:
            driver.execute_script(f"window.scrollBy(0, {random.randint(300, 600)});")
            time.sleep(random.uniform(5.0, 15.0))
        print("阅读完成！")

    except Exception as e:
        print(f"出错: {e}")
    finally:
        driver.quit()
