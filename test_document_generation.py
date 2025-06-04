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

def test_document_generation():
    """测试文档生成功能"""
    print("开始测试文档生成功能...")
    
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
    
    # 2. 确认需求分析阶段
    print("\n2. 确认需求分析阶段")
    response = requests.post(
        f"{BASE_URL}/seminar/1/phase/需求分析/action",
        json={"action": "continue"}
    )
    print_response(response)
    
    # 3. 获取需求分析文档
    print("\n3. 获取需求分析文档")
    response = requests.get(
        f"{BASE_URL}/seminar/1/phase/需求分析/document"
    )
    print_response(response)
    
    # 4. 预览需求分析文档
    print("\n4. 预览需求分析文档")
    response = requests.get(
        f"{BASE_URL}/seminar/1/phase/需求分析/document/preview"
    )
    print_response(response)
    
    # 5. 获取文档版本历史
    print("\n5. 获取文档版本历史")
    response = requests.get(
        f"{BASE_URL}/seminar/1/phase/需求分析/document/versions"
    )
    print_response(response)
    
    # 6. 导出需求分析文档
    print("\n6. 导出需求分析文档")
    response = requests.get(
        f"{BASE_URL}/seminar/1/phase/需求分析/document/export"
    )
    if response.status_code == 200:
        filename = f"需求分析_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"文档已导出到: {filename}")
    else:
        print_response(response)
    
    # 7. 创建系统设计阶段
    print("\n7. 创建系统设计阶段")
    phase_data = {
        "task_prompt": "设计在线购物系统的架构和技术方案",
        "role_settings": json.dumps({
            "architect": "系统架构师",
            "developer": "开发工程师",
            "dba": "数据库管理员"
        }),
        "phase_conclusion": "采用前后端分离架构，前端使用Vue.js框架，后端使用Spring Boot框架。数据库使用MySQL，缓存使用Redis。采用微服务架构，将系统拆分为用户服务、商品服务、订单服务等模块。"
    }
    response = requests.post(
        f"{BASE_URL}/seminar/1/phase/系统设计",
        json=phase_data
    )
    print_response(response)
    
    # 8. 确认系统设计阶段
    print("\n8. 确认系统设计阶段")
    response = requests.post(
        f"{BASE_URL}/seminar/1/phase/系统设计/action",
        json={"action": "continue"}
    )
    print_response(response)
    
    # 9. 预览系统设计文档
    print("\n9. 预览系统设计文档")
    response = requests.get(
        f"{BASE_URL}/seminar/1/phase/系统设计/document/preview"
    )
    print_response(response)
    
    # 10. 创建编码实现阶段
    print("\n10. 创建编码实现阶段")
    phase_data = {
        "task_prompt": "实现用户注册和登录功能",
        "role_settings": json.dumps({
            "developer": "后端开发",
            "frontend": "前端开发",
            "tester": "测试工程师"
        }),
        "phase_conclusion": "已完成用户注册和登录功能的实现，包括前端表单验证、后端API接口、数据库操作等。实现了密码加密存储、JWT token认证等功能。通过了单元测试和集成测试。"
    }
    response = requests.post(
        f"{BASE_URL}/seminar/1/phase/编码实现",
        json=phase_data
    )
    print_response(response)
    
    # 11. 确认编码实现阶段
    print("\n11. 确认编码实现阶段")
    response = requests.post(
        f"{BASE_URL}/seminar/1/phase/编码实现/action",
        json={"action": "continue"}
    )
    print_response(response)
    
    # 12. 预览编码实现文档
    print("\n12. 预览编码实现文档")
    response = requests.get(
        f"{BASE_URL}/seminar/1/phase/编码实现/document/preview"
    )
    print_response(response)
    
    # 13. 测试重新执行功能
    print("\n13. 测试重新执行功能")
    response = requests.post(
        f"{BASE_URL}/seminar/1/phase/编码实现/action",
        json={
            "action": "restart",
            "restart_prompt": "需要添加手机号验证功能"
        }
    )
    print_response(response)
    
    print("\n文档生成功能测试完成！")

if __name__ == "__main__":
    # 确保服务器正在运行
    try:
        response = requests.get("http://127.0.0.1:8000/")
        if response.status_code == 200:
            test_document_generation()
        else:
            print("服务器未正常运行，请先启动服务器：python visualizer/app.py")
    except requests.exceptions.ConnectionError:
        print("无法连接到服务器，请确保服务器正在运行：python visualizer/app.py") 