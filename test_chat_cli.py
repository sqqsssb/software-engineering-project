import argparse
import json
import requests
import time
from datetime import datetime

def print_response(response):
    """打印响应内容"""
    print(f"状态码: {response.status_code}")
    try:
        if response.headers.get('content-type') == 'application/json':
            print("响应内容:")
            print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        else:
            print("响应内容:")
            print(response.text)
    except json.JSONDecodeError:
        print("响应内容:")
        print(response.text)
    print("-" * 50)

def test_chat_and_control(base_url, seminar_id, phase_name):
    """测试聊天和用户控制功能"""
    print("开始测试聊天和用户控制功能...\n")

    # 1. 创建需求分析阶段
    print("1. 创建需求分析阶段")
    phase_data = {
        "task_prompt": "开发一个在线购物系统，需要支持用户注册、商品浏览、购物车、订单管理等功能",
        "role_settings": json.dumps({
            "analyst": "需求分析师",
            "user": "客户代表",
            "developer": "开发工程师"
        }),
        "phase_conclusion": "系统需要包含用户管理、商品管理、购物车、订单管理、支付集成等核心功能模块。用户界面需要简洁直观，支持响应式设计。系统需要保证数据安全和交易安全。"
    }
    response = requests.post(f"{base_url}/seminar/{seminar_id}/phase/{phase_name}", json=phase_data)
    print_response(response)

    # 2. 测试聊天功能
    print("2. 测试聊天功能")
    chat_data = {
        "message": "请详细说明用户管理模块需要实现哪些具体功能？"
    }
    response = requests.post(f"{base_url}/seminar/{seminar_id}/phase/{phase_name}/chat", json=chat_data)
    print_response(response)

    # 3. 测试检索记忆功能（用户不修改）
    print("3. 测试检索记忆功能（用户不修改）")
    control_data = {
        "action": "retrieve"
    }
    response = requests.post(f"{base_url}/seminar/{seminar_id}/phase/{phase_name}/control", json=control_data)
    print_response(response)

    # 4. 测试更新结论功能（用户修改）
    print("4. 测试更新结论功能（用户修改）")
    control_data = {
        "action": "update",
        "conclusion": "系统需要包含用户管理、商品管理、购物车、订单管理、支付集成等核心功能模块。用户界面需要简洁直观，支持响应式设计。系统需要保证数据安全和交易安全。同时需要支持用户角色管理和权限控制。"
    }
    response = requests.post(f"{base_url}/seminar/{seminar_id}/phase/{phase_name}/control", json=control_data)
    print_response(response)

    # 5. 验证更新后的结论
    print("5. 验证更新后的结论")
    response = requests.get(f"{base_url}/seminar/{seminar_id}/phase/{phase_name}")
    print_response(response)

    print("\n聊天和用户控制功能测试完成！")

def main():
    parser = argparse.ArgumentParser(description='测试聊天和用户控制功能')
    parser.add_argument('--url', type=str, default="http://localhost:5000",
                        help="API服务器的基础URL")
    parser.add_argument('--seminar', type=int, default=1,
                        help="研讨会ID")
    parser.add_argument('--phase', type=str, default="需求分析",
                        help="阶段名称")
    args = parser.parse_args()

    test_chat_and_control(args.url, args.seminar, args.phase)

if __name__ == "__main__":
    main() 