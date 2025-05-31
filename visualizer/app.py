import logging
import subprocess
import threading

import requests
import os
from flask import Flask, send_from_directory, request, jsonify
import argparse

app = Flask(__name__, static_folder='static')
run_lock = threading.Lock()  # 定义锁
request_count = 0  # 确保全局变量在顶层初始化
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
        print(f"收到第 {request_count} 次请求，Prompt: {request.form.get('prompt')}")
        print(f"客户端 IP: {request.remote_addr}")
        try:
            prompt = request.form.get("prompt")
            if not prompt:
                return jsonify({"status": "error", "message": "Prompt is required"}), 400

            # 直接调用虚拟环境的 Python 解释器
            python_path = "D:/Anaconda3/envs/ChatDev_conda_env/python.exe"  # Windows 路径

            result = subprocess.run(
                [python_path, "run.py", "--task", prompt],  # 直接用虚拟环境的 Python 执行
                capture_output=True,
                text=True,
                encoding='utf-8',  # 强制用 utf-8 解码，替代系统默认编码
                timeout=300,
                cwd="D:/ChatDev-main/ChatDev-main"  # run.py 所在目录
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='argparse')
    parser.add_argument('--port', type=int, default=8000, help="port")
    args = parser.parse_args()
    port.append(args.port)
    print(f"Please visit http://127.0.0.1:{port[-1]}/ for the front-end display page. \nIn the event of a port conflict, please modify the port argument (e.g., python3 app.py --port 8012).")
    app.run(host='0.0.0.0', debug=False, port=port[-1])
