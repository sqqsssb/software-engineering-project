import logging
import subprocess
import threading
import sys
from pathlib import Path

import requests
import os
from flask import Flask, send_from_directory, request, jsonify
import argparse

app = Flask(__name__, static_folder='static')
run_lock = threading.Lock()  # 定义锁
request_count = 0  # 确保全局变量在顶层初始化

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:gwh0417##@localhost/chatdev'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

# 注册API蓝图
app.register_blueprint(api, url_prefix='/api')

# 其他配置
run_lock = threading.Lock()
request_count = 0
app.logger.setLevel(logging.ERROR)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
messages = []
port = [8000]

def send_msg(role, text):
    try:
        data = {"role": role, "text": text}
        response = requests.post(f"http://127.0.0.1:{port[-1]}/send_message", json=data)
    except:
        logging.info("flask app.py did not start for online log")


@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/chain_visualizer")
def chain_visualizer():
    return send_from_directory("static", "chain_visualizer.html")

@app.route("/replay")
def replay():
    return send_from_directory("static", "replay.html")

@app.route("/get_messages")
def get_messages():
    return jsonify(messages)

@app.route("/send_message", methods=["POST"])
def send_message():
    data = request.get_json()
    role = data.get("role")
    text = data.get("text")

    avatarUrl = find_avatar_url(role)

    message = {"role": role, "text": text, "avatarUrl": avatarUrl}
    messages.append(message)
    return jsonify(message)

@app.route("/run_prompt", methods=["POST"])
def run_prompt():
    with run_lock:  # 加锁，确保同一时间只有一个请求执行
        global request_count
        request_count += 1
        print(f"收到第 {request_count} 次请求，Prompt: {request.form.get('prompt')}, Name: {request.form.get('name')}, Model: {request.form.get('model')}, Path: {request.form.get('path')}, Config: {request.form.get('config')}, Org: {request.form.get('org')}")
        print(f"客户端 IP: {request.remote_addr}")
        try:
            prompt = request.form.get("prompt")
            name = request.form.get("name")  # 新增：获取 name 参数
            model = request.form.get("model")  # 新增：获取 model 参数
            path = request.form.get("path")    # 新增：获取 path 参数
            config = request.form.get("config") 
            org = request.form.get("org") 

            if not prompt:
                return jsonify({"status": "error", "message": "Prompt is required"}), 400
            
            if not name:  # 新增：校验 name
                return jsonify({"status": "error", "message": "Name is required"}), 400
            
            if not model:
                return jsonify({"status": "error", "message": "Model is required"}), 400

            # 直接调用虚拟环境的 Python 解释器
            # python_path = "D:/Anaconda3/envs/ChatDev_conda_env/python.exe"  # Windows 路径
            # python_path="D:/tools/Anaconda/envs/ChatDev_conda_env/python.exe"
            python_path=sys.executable
            print(f"python_path:{python_path}")
            project_root = Path(__file__).parent.parent
            print(f"project_root:{project_root}")

            result = subprocess.run(
                [python_path, "run.py", 
                 "--task", prompt,
                 "--name", name,
                 "--model", model,  # 新增：传递 model 参数
                 "--path", path,
                 "--config", config,  # 新增：传递 config 参数
                 "--org", org],       # 新增：传递 org 参数],   # 新增：传递 path 参数
                capture_output=True,
                text=True,
                encoding='utf-8',  # 强制用 utf-8 解码，替代系统默认编码
                timeout=300,
                # cwd="D:/ChatDev-main/ChatDev-main"  # run.py 所在目录
                # cwd="D:/projects/software-engineering-project-main"
                cwd = project_root
            )

            # 重点：打印 run.py 的输出和错误
            print("run.py 标准输出:", result.stdout)
            print("run.py 错误输出:", result.stderr)

            if result.returncode != 0:
                print(result.returncode)
                return jsonify({
                    "status": "error",
                    "message": "Script execution failed",
                    "error_output": result.stderr
                }), 500

            return jsonify({"status": "success", "message": "Script started successfully"}), 200

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

def find_avatar_url(role):
    role = role.replace(" ", "%20")
    avatar_filename = f"avatars/{role}.png"
    avatar_url = f"/static/{avatar_filename}"
    return avatar_url

@app.route('/api/phase/control', methods=['POST'])
def phase_control():
    current_phase = get_current_phase()
    data = request.json
    action = data.get('action')
    
    if not current_phase:
        return jsonify({'error': 'No active phase'}), 400
        
    if action == 'continue':
        # 继续执行当前阶段
        return jsonify({
            'status': 'success',
            'message': 'Continuing phase execution',
            'phase_state': current_phase.get_phase_state()
        })
    elif action == 'restart':
        # 重新执行当前阶段
        restart_prompt = data.get('restart_prompt')
        current_phase.update_phase_state(
            needs_restart=True,
            restart_prompt=restart_prompt
        )
        return jsonify({
            'status': 'success',
            'message': 'Phase will be restarted',
            'phase_state': current_phase.get_phase_state()
        })
    else:
        return jsonify({'error': 'Invalid action'}), 400

@app.route('/api/phase/state', methods=['GET'])
def get_phase_state():
    current_phase = get_current_phase()
    if not current_phase:
        return jsonify({'error': 'No active phase'}), 400
        
    return jsonify({
        'status': 'success',
        'phase_state': current_phase.get_phase_state()
    })

@app.route('/api/phase/set_state', methods=['POST'])
def set_phase_state():
    """设置当前阶段状态"""
    try:
        state_data = request.json
        if not state_data:
            return jsonify({'error': 'No state data provided'}), 400
            
        # 创建一个新的阶段实例
        phase = TestPhase(
            assistant_role_name=state_data.get('assistant_role_name', '测试助手'),
            user_role_name=state_data.get('user_role_name', '测试用户'),
            phase_prompt=state_data.get('phase_prompt', '这是一个测试阶段'),
            phase_name=state_data.get('phase_name', '测试阶段'),
            assistant_role_prompt=state_data.get('assistant_role_prompt', '你是一个测试助手'),
            user_role_prompt=state_data.get('user_role_prompt', '你是一个测试用户'),
            model_type=ModelType.GPT_4
        )
        
        # 更新阶段状态
        phase.update_phase_state(
            task_prompt=state_data.get('task_prompt'),
            current_turn=state_data.get('current_turn', 0),
            is_completed=state_data.get('is_completed', False),
            needs_restart=state_data.get('needs_restart', False),
            restart_prompt=state_data.get('restart_prompt')
        )
        
        # 设置为当前阶段
        set_current_phase(phase)
        
        return jsonify({
            'status': 'success',
            'message': 'Phase state set successfully',
            'phase_state': phase.get_phase_state()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='argparse')
    parser.add_argument('--port', type=int, default=8000, help="port")
    args = parser.parse_args()
    port.append(args.port)
    print(f"Please visit http://127.0.0.1:{port[-1]}/ for the front-end display page. \nIn the event of a port conflict, please modify the port argument (e.g., python3 app.py --port 8012).")
    app.run(host='0.0.0.0', debug=False, port=port[-1])
