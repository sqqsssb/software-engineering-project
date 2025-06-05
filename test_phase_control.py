import requests
import json
from chatdev.phase import Phase
from chatdev.phase_state import set_current_phase
from camel.typing import ModelType

class TestPhase(Phase):
    """测试用的具体 Phase 实现"""
    def update_chat_env(self, chat_env):
        """更新聊天环境"""
        pass  # 测试中不需要实际更新环境

    def update_phase_env(self, phase_env):
        """更新阶段环境"""
        pass  # 测试中不需要实际更新环境

def create_test_phase():
    """创建一个测试阶段实例"""
    phase = TestPhase(
        assistant_role_name="测试助手",
        user_role_name="测试用户",
        phase_prompt="这是一个测试阶段",
        phase_name="测试阶段",
        assistant_role_prompt="你是一个测试助手",
        user_role_prompt="你是一个测试用户",
        model_type=ModelType.GPT_4
    )
    # 设置初始状态
    phase.update_phase_state(
        task_prompt="测试任务",
        current_turn=0,
        is_completed=False,
        needs_restart=False
    )
    return phase

def test_phase_control():
    print("开始测试阶段用户控制功能...\n")
    
    # 检查服务器是否运行
    try:
        response = requests.get("http://127.0.0.1:8000/")
        if response.status_code != 200:
            print("错误：Flask 服务器未正常运行")
            return
    except requests.exceptions.ConnectionError:
        print("错误：无法连接到 Flask 服务器，请确保服务器正在运行")
        return
    
    # 创建测试阶段
    test_phase = create_test_phase()
    
    # 通过 API 设置阶段状态
    print("设置阶段状态...")
    try:
        state_data = test_phase.get_phase_state()
        print(f"发送的状态数据: {json.dumps(state_data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(
            "http://127.0.0.1:8000/api/phase/set_state",
            json=state_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"服务器响应状态码: {response.status_code}")
        print(f"服务器响应内容: {response.text}")
        
        if response.status_code != 200:
            print(f"设置阶段状态失败: {response.text}")
            return
            
        response_data = response.json()
        print(f"阶段状态设置成功: {json.dumps(response_data, ensure_ascii=False, indent=2)}\n")
        
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {str(e)}")
        return
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {str(e)}")
        print(f"服务器响应内容: {response.text}")
        return
    except Exception as e:
        print(f"未知错误: {str(e)}")
        return
    
    # 测试1：获取阶段状态
    print("测试1：获取阶段状态")
    try:
        response = requests.get("http://127.0.0.1:8000/api/phase/state")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.json()}\n")
    except Exception as e:
        print(f"获取阶段状态失败: {str(e)}\n")
    
    # 测试2：继续执行阶段
    print("测试2：继续执行阶段")
    try:
        response = requests.post(
            "http://127.0.0.1:8000/api/phase/control",
            json={"action": "continue"}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.json()}\n")
    except Exception as e:
        print(f"继续执行阶段失败: {str(e)}\n")
    
    # 测试3：重新执行阶段（带提示）
    print("测试3：重新执行阶段（带提示）")
    try:
        response = requests.post(
            "http://127.0.0.1:8000/api/phase/control",
            json={
                "action": "restart",
                "restart_prompt": "新的测试提示"
            }
        )
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.json()}\n")
    except Exception as e:
        print(f"重新执行阶段（带提示）失败: {str(e)}\n")
    
    # 测试4：重新执行阶段（无提示）
    print("测试4：重新执行阶段（无提示）")
    try:
        response = requests.post(
            "http://127.0.0.1:8000/api/phase/control",
            json={"action": "restart"}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.json()}\n")
    except Exception as e:
        print(f"重新执行阶段（无提示）失败: {str(e)}\n")
    
    # 测试5：无效操作
    print("测试5：无效操作")
    try:
        response = requests.post(
            "http://127.0.0.1:8000/api/phase/control",
            json={"action": "invalid_action"}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.json()}\n")
    except Exception as e:
        print(f"无效操作测试失败: {str(e)}\n")
    
    print("测试完成！")

if __name__ == "__main__":
    test_phase_control() 