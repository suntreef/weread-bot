import json, os, threading
from flask import Flask, render_template, request, jsonify, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
from bot import start_reading, check_login_and_get_qr

app = Flask(__name__)
CONFIG_FILE = 'data/config.json'
LOG_FILE = 'data/run.log'
scheduler = BackgroundScheduler()

# 新增了 push_token 默认配置
default_config = {"book_url": "", "reading_minutes": 1, "schedule_time": "08:30", "push_token": ""}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return default_config

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(config, f, ensure_ascii=False, indent=4)

def run_job():
    config = load_config()
    start_reading(config.get('book_url', ''), int(config['reading_minutes']), config.get('push_token', ''))

def update_schedule():
    config = load_config()
    time_parts = config['schedule_time'].split(':')
    scheduler.remove_all_jobs()
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

@app.route('/api/check_login', methods=['POST'])
def check_login():
    threading.Thread(target=check_login_and_get_qr).start()
    return jsonify({"status": "success", "message": "已触发登录检测，请查看下方日志！"})

@app.route('/api/run_now', methods=['POST'])
def run_now():
    threading.Thread(target=run_job).start()
    return jsonify({"status": "success", "message": "阅读任务已启动，请查看下方日志！"})

@app.route('/api/get_logs', methods=['GET'])
def get_logs():
    if not os.path.exists(LOG_FILE): return jsonify({"logs": "暂无日志...\n"})
    with open(LOG_FILE, 'r', encoding='utf-8') as f: lines = f.readlines()
    return jsonify({"logs": "".join(lines[-40:])}) # 展示最后40行

@app.route('/api/clear_logs', methods=['POST'])
def clear_logs():
    if os.path.exists(LOG_FILE): os.remove(LOG_FILE)
    return jsonify({"status": "success", "message": "日志已清空！"})

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    if not os.path.exists(CONFIG_FILE): save_config(default_config)
    update_schedule()
    scheduler.start()
    app.run(host='0.0.0.0', port=3666)
