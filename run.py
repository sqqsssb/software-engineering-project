# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.1
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
import argparse
import logging
import os
import sys
import json
import requests
from datetime import datetime

from camel.typing import ModelType

root = os.path.dirname(__file__)
sys.path.append(root)

from chatdev.chat_chain import ChatChain

try:
    from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
    from openai.types.chat.chat_completion_message import FunctionCall

    openai_new_api = True  # new openai api version
except ImportError:
    openai_new_api = False  # old openai api version
    print(
        "Warning: Your OpenAI version is outdated. \n "
        "Please update as specified in requirement.txt. \n "
        "The old API interface is deprecated and will no longer be supported.")


def get_config(company):
    """
    return configuration json files for ChatChain
    user can customize only parts of configuration json files, other files will be left for default
    Args:
        company: customized configuration name under CompanyConfig/

    Returns:
        path to three configuration jsons: [config_path, config_phase_path, config_role_path]
    """
    config_dir = os.path.join(root, "CompanyConfig", company)
    default_config_dir = os.path.join(root, "CompanyConfig", "Default")

    config_files = [
        "ChatChainConfig.json",
        "PhaseConfig.json",
        "RoleConfig.json"
    ]

    config_paths = []

    for config_file in config_files:
        company_config_path = os.path.join(config_dir, config_file)
        default_config_path = os.path.join(default_config_dir, config_file)

        if os.path.exists(company_config_path):
            config_paths.append(company_config_path)
        else:
            config_paths.append(default_config_path)

    return tuple(config_paths)

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

parser = argparse.ArgumentParser(description='argparse')
parser.add_argument('--config', type=str, default="Online_Shopping_System",
                    help="Name of config, which is used to load configuration under CompanyConfig/")
parser.add_argument('--org', type=str, default="DefaultOrganization",
                    help="Name of organization, your software will be generated in WareHouse/name_org_timestamp")
parser.add_argument('--task', type=str, default="say hi in python.",
                    help="Prompt of software")
parser.add_argument('--name', type=str, default="hello",
                    help="Name of software, your software will be generated in WareHouse/name_org_timestamp")
parser.add_argument('--model', type=str, default="GPT_4O_MINI",
                    help="GPT Model, choose from {'GPT_3_5_TURBO', 'GPT_4', 'GPT_4_TURBO', 'GPT_4O', 'GPT_4O_MINI'}")
parser.add_argument('--path', type=str, default="",
                    help="Your file directory, ChatDev will build upon your software in the Incremental mode")
parser.add_argument('--mode', type=str, default="normal",
                    help="运行模式：normal（正常模式）或 chat（聊天模式）")
parser.add_argument('--url', type=str, default="http://localhost:5000",
                    help="API服务器的基础URL（仅在聊天模式下使用）")
parser.add_argument('--seminar', type=int, default=1,
                    help="研讨会ID（仅在聊天模式下使用）")
parser.add_argument('--phase', type=str, default="需求分析",
                    help="阶段名称（仅在聊天模式下使用）")
args = parser.parse_args()

if args.mode == "chat":
    # 聊天模式
    test_chat_and_control(args.url, args.seminar, args.phase)
else:
    # 正常模式
    # ----------------------------------------
    #          Init ChatChain
    # ----------------------------------------
    config_path, config_phase_path, config_role_path = get_config(args.config)
    args2type = {'GPT_3_5_TURBO': ModelType.GPT_3_5_TURBO,
                 'GPT_4': ModelType.GPT_4,
                #  'GPT_4_32K': ModelType.GPT_4_32k,
                 'GPT_4_TURBO': ModelType.GPT_4_TURBO,
                #  'GPT_4_TURBO_V': ModelType.GPT_4_TURBO_V
                 'GPT_4O': ModelType.GPT_4O,
                 'GPT_4O_MINI': ModelType.GPT_4O_MINI,
                 }
    if openai_new_api:
        args2type['GPT_3_5_TURBO'] = ModelType.GPT_3_5_TURBO_NEW

    chat_chain = ChatChain(config_path=config_path,
                           config_phase_path=config_phase_path,
                           config_role_path=config_role_path,
                           task_prompt=args.task,
                           project_name=args.name,
                           org_name=args.org,
                           model_type=args2type[args.model],
                           code_path=args.path)

    # ----------------------------------------
    #          Init Log
    # ----------------------------------------
    logging.basicConfig(filename=chat_chain.log_filepath, level=logging.INFO,
                        format='[%(asctime)s %(levelname)s] %(message)s',
                        datefmt='%Y-%d-%m %H:%M:%S', encoding="utf-8")

    # ----------------------------------------
    #          Pre Processing
    # ----------------------------------------

    chat_chain.pre_processing()

    # ----------------------------------------
    #          Personnel Recruitment
    # ----------------------------------------

    chat_chain.make_recruitment()

    # ----------------------------------------
    #          Chat Chain
    # ----------------------------------------

    chat_chain.execute_chain()

    # ----------------------------------------
    #          Post Processing
    # ----------------------------------------

    chat_chain.post_processing()
