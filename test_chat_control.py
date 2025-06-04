import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api"

def print_response(response):
    """打印响应内容"""
    print(f"状态码: {response.status_code}")
    print("响应内容:")
    try:
        if response.headers.get('content-type', '').startswith('application/json'):
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(response.text)
    except json.JSONDecodeError:
        print("无法解析JSON响应:")
        print(response.text)
    print("-" * 50)

def test_chat_and_control():
    """测试聊天和用户控制功能"""
    print("开始测试聊天和用户控制功能...")
    
    # 1. 创建需求分析阶段
    print("\n1. 创建需求分析阶段")
    phase_data = {
        "task_prompt": "开发一个在线购物系统，需要支持用户注册、商品浏览、购物车、订单管理等功能",
        "role_settings": json.dumps({
            "analyst": "需求分析师",
            "user": "客户代表",
            "developer": "开发工程师"
        }),
        "phase_conclusion": "系统需要包含用户管理、商品管理、购物车、订单管理、支付集成等核心功能模块。用户界面需要简洁直观，支持响应式设计。系统需要保证数据安全和交易安全。"
    }
    response = requests.post(
        f"{BASE_URL}/seminar/1/phase/需求分析",
        json=phase_data
    )
    print_response(response)
    
    # 2. 测试聊天功能
    print("\n2. 测试聊天功能")
    chat_data = {
        "message": "请详细说明用户管理模块的功能需求"
    }
    response = requests.post(
        f"{BASE_URL}/seminar/1/phase/需求分析/chat",
        json=chat_data
    )
    print_response(response)
    
    # 3. 测试检索记忆功能（用户不修改）
    print("\n3. 测试检索记忆功能（用户不修改）")
    control_data = {
        "action": "retrieve"
    }
    response = requests.post(
        f"{BASE_URL}/seminar/1/phase/需求分析/control",
        json=control_data
    )
    print_response(response)
    
    # 4. 测试更新结论功能（用户修改）
    print("\n4. 测试更新结论功能（用户修改）")
    new_conclusion = "系统需要包含用户管理、商品管理、购物车、订单管理、支付集成等核心功能模块。用户界面需要简洁直观，支持响应式设计。系统需要保证数据安全和交易安全。同时需要支持用户角色管理和权限控制。"
    control_data = {
        "action": "update",
        "conclusion": new_conclusion
    }
    response = requests.post(
        f"{BASE_URL}/seminar/1/phase/需求分析/control",
        json=control_data
    )
    print_response(response)
    
    # 5. 验证更新后的结论
    print("\n5. 验证更新后的结论")
    response = requests.get(
        f"{BASE_URL}/seminar/1/phase/需求分析"
    )
    print_response(response)
    
    print("\n聊天和用户控制功能测试完成！")

if __name__ == "__main__":
    # 确保服务器正在运行
    try:
        response = requests.get("http://127.0.0.1:8000/")
        if response.status_code == 200:
            test_chat_and_control()
        else:
            print("服务器未正常运行，请先启动服务器：python visualizer/app.py")
    except requests.exceptions.ConnectionError:
        print("无法连接到服务器，请确保服务器正在运行：python visualizer/app.py") 