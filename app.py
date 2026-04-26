import json, os, threading
from flask import Flask, render_template, request, jsonify, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
from bot import start_reading

app = Flask(__name__)
CONFIG_FILE = 'data/config.json'
scheduler = BackgroundScheduler()

default_config = {"book_url": "https://weread.qq.com/web/reader/xxxxxx", "reading_minutes": 1, "schedule_time": "08:30"}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return default_config

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(config, f, ensure_ascii=False, indent=4)

def run_job():
    config = load_config()
    start_reading(config['book_url'], int(config['reading_minutes']))

def update_schedule():
    config = load_config()
    time_parts = config['schedule_time'].split(':')
    scheduler.remove_all_jobs() # 这里也包含了之前的修复
    scheduler.add_job(run_job, 'cron', hour=int(time_parts[0]), minute=int(time_parts[1]), id='read_job')

@app.route('/')
def index():
    qr_exists = os.path.exists('data/qrcode.png')
    return render_template('index.html', config=load_config(), qr_exists=qr_exists)

@app.route('/data/<path:filename>')
def serve_data(filename):
    return send_from_directory('data', filename)

@app.route('/api/save', methods=['POST'])
def save():
    save_config(request.json)
    update_schedule()
    return jsonify({"status": "success", "message": "配置已保存，定时任务已更新！"})

@app.route('/api/run_now', methods=['POST'])
def run_now():
    # 使用原生线程强制立即触发，避免调度器延迟卡顿
    threading.Thread(target=run_job).start()
    return jsonify({"status": "success", "message": "已在后台极速启动！请等待 10-15 秒后刷新页面查看二维码。"})

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    if not os.path.exists(CONFIG_FILE): save_config(default_config)
    update_schedule()
    scheduler.start()
    app.run(host='0.0.0.0', port=3666)
