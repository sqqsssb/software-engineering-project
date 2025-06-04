import logging
import subprocess
import threading
import requests
import os
from flask import Flask, send_from_directory, request, jsonify, render_template
import argparse
from flask_socketio import SocketIO
from chatdev.phase_state import get_current_phase, set_current_phase
from chatdev.phase import Phase
from camel.typing import ModelType
from visualizer.models import db
from visualizer.api import api

class TestPhase(Phase):
    """测试用的具体 Phase 实现"""
    def update_chat_env(self, chat_env):
        """更新聊天环境"""
        pass  # 测试中不需要实际更新环境

    def update_phase_env(self, phase_env):
        """更新阶段环境"""
        pass  # 测试中不需要实际更新环境

app = Flask(__name__, static_folder='static')
socketio = SocketIO(app)

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

# 创建数据库表
with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template('index.html')

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
    with run_lock:
        global request_count
        request_count += 1
        print(f"收到第 {request_count} 次请求，Prompt: {request.form.get('prompt')}")
        print(f"客户端 IP: {request.remote_addr}")
        try:
            prompt = request.form.get("prompt")
            if not prompt:
                return jsonify({"status": "error", "message": "Prompt is required"}), 400

            python_path = "D:/Anaconda3/envs/ChatDev_conda_env/python.exe"

            result = subprocess.run(
                [python_path, "run.py", "--task", prompt],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300,
                cwd="D:/ChatDev-main/ChatDev-main"
            )

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
    socketio.run(app, host='0.0.0.0', debug=False, port=port[-1])
