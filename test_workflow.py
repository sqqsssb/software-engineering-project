import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api"

def print_response(response):
    """打印响应内容"""
    print(f"状态码: {response.status_code}")
    print("响应内容:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print("-" * 50)

def test_workflow():
    """测试完整工作流程"""
    print("开始测试工作流程...")
    
    # 1. 创建需求分析阶段
    print("\n1. 创建需求分析阶段")
    phase_data = {
        "task_prompt": "开发一个在线购物系统",
        "role_settings": json.dumps({
            "analyst": "需求分析师",
            "user": "客户代表"
        }),
        "phase_conclusion": "系统需要包含用户注册、商品浏览、购物车、订单管理等功能"
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
        filename = f"需求分析_{time.strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"文档已导出到: {filename}")
    else:
        print_response(response)
    
    # 7. 创建系统设计阶段
    print("\n7. 创建系统设计阶段")
    phase_data = {
        "task_prompt": "设计在线购物系统的架构",
        "role_settings": json.dumps({
            "architect": "系统架构师",
            "developer": "开发工程师"
        }),
        "phase_conclusion": "采用前后端分离架构，使用Spring Boot + Vue.js技术栈"
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
        "task_prompt": "实现用户注册功能",
        "role_settings": json.dumps({
            "developer": "后端开发",
            "tester": "测试工程师"
        }),
        "phase_conclusion": "已完成用户注册API和前端表单的实现，并通过单元测试"
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
    
    print("\n工作流程测试完成！")

if __name__ == "__main__":
    # 确保服务器正在运行
    try:
        response = requests.get("http://127.0.0.1:8000/")
        if response.status_code == 200:
            test_workflow()
        else:
            print("服务器未正常运行，请先启动服务器：python visualizer/app.py")
    except requests.exceptions.ConnectionError:
        print("无法连接到服务器，请确保服务器正在运行：python visualizer/app.py") 