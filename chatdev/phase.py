import json
import os
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

import mysql
from mysql.connector import Error

from camel.agents import RolePlaying, ChatAgent
from camel.messages import ChatMessage
from camel.typing import TaskType, ModelType, RoleType
from chatdev.chat_env import ChatEnv
from chatdev.statistics import get_info
from chatdev.utils import log_visualize, log_arguments
from ecl import memory
from ecl.db_config import create_connection, close_connection
from ecl.memory import MemoryBase
from chatdev.phase_state import set_current_phase
from visualizer.api import generate_document


class Phase(ABC):

    def __init__(self,
                 assistant_role_name: str,
                 user_role_name: str,
                 phase_prompt: str,
                 phase_name: str,
                 assistant_role_prompt: str,
                 user_role_prompt: str,
                 model_type: ModelType = ModelType.GPT_4,
                 phase_env: Dict = None,
                 phase_env_template: Dict = None,
                 reflection_prompt: str = None,
                 ceo_prompt: str = None,
                 counselor_prompt: str = None,
                 role_prompts: Dict = None,
                 log_filepath: str = None,
                 ):
        """

        Args:
            assistant_role_name: who receives chat in a phase
            user_role_name: who starts the chat in a phase
            phase_prompt: prompt of this phase
            phase_name: name of this phase
            assistant_role_prompt: prompt for assistant role
            user_role_prompt: prompt for user role
            model_type: type of model to use
            phase_env: environment variables for this phase
            phase_env_template: template for phase environment
            reflection_prompt: prompt for reflection
            ceo_prompt: prompt for CEO role
            counselor_prompt: prompt for counselor role
            role_prompts: prompts for all roles
            log_filepath: path to the log file
        """
        self.assistant_role_name = assistant_role_name
        self.user_role_name = user_role_name
        self.phase_prompt = phase_prompt
        self.phase_name = phase_name
        self.assistant_role_prompt = assistant_role_prompt
        self.user_role_prompt = user_role_prompt
        self.model_type = model_type
        self.phase_env = phase_env if phase_env is not None else {}
        self.phase_env_template = phase_env_template if phase_env_template is not None else {}
        self.reflection_prompt = reflection_prompt
        self.ceo_prompt = ceo_prompt
        self.counselor_prompt = counselor_prompt
        self.role_prompts = role_prompts if role_prompts is not None else {}
        self.log_filepath = log_filepath
        self.seminar_conclusion = None
        # 添加状态管理相关的属性
        self.phase_state = {
            'task_prompt': None,
            'current_turn': 0,
            'is_completed': False,
            'needs_restart': False,
            'restart_prompt': None
        }
        self.max_retries = 3
        # 设置当前阶段实例
        set_current_phase(self)

    def get_phase_state(self):
        """获取当前阶段的状态"""
        return self.phase_state

    def update_phase_state(self, **kwargs):
        """更新阶段状态"""
        self.phase_state.update(kwargs)

    def reset_phase_state(self):
        """重置阶段状态"""
        self.phase_state.update({
            'current_turn': 0,
            'is_completed': False,
            'needs_restart': False,
            'restart_prompt': None
        })

    @log_arguments
    def chatting(
            self,
            chat_env,
            task_prompt: str,
            assistant_role_name: str,
            user_role_name: str,
            phase_prompt: str,
            phase_name: str,
            assistant_role_prompt: str,
            user_role_prompt: str,
            task_type=TaskType.CHATDEV,
            need_reflect=True,
            with_task_specify=False,
            model_type=ModelType.GPT_4O_MINI,
            memory=None,
            placeholders=None,
            chat_turn_limit=10
    ) -> str:

        if placeholders is None:
            placeholders = {}
        assert 1 <= chat_turn_limit <= 100

        if not chat_env.exist_employee(assistant_role_name):
            raise ValueError(f"{assistant_role_name} not recruited in ChatEnv.")
        if not chat_env.exist_employee(user_role_name):
            raise ValueError(f"{user_role_name} not recruited in ChatEnv.")

        # 更新阶段状态
        self.update_phase_state(
            task_prompt=task_prompt,
            current_turn=0,
            is_completed=False
        )

        # 确保角色提示不为 None
        if assistant_role_prompt is None:
            assistant_role_prompt = self.role_prompts.get(assistant_role_name, "")
        if user_role_prompt is None:
            user_role_prompt = self.role_prompts.get(user_role_name, "")

        print(f"RolePlaying初始化时的phase_name：{phase_name}")
        # init role play
        role_play_session = RolePlaying(
            assistant_role_name=assistant_role_name,
            user_role_name=user_role_name,
            assistant_role_prompt=assistant_role_prompt,
            user_role_prompt=user_role_prompt,
            task_prompt=task_prompt,
            task_type=task_type,
            with_task_specify=with_task_specify,
            memory=memory,
            model_type=model_type,
            background_prompt=chat_env.config.background_prompt,
            phase_name = phase_name,
        )
        log_visualize("System", role_play_session.assistant_sys_msg)
        log_visualize("System", role_play_session.user_sys_msg)

        # start the chat
        _, input_user_msg = role_play_session.init_chat(None, placeholders, phase_prompt)
        seminar_conclusion = None
        # 检查是否需要重新开始
        if self.phase_state['needs_restart']:
            if self.phase_state['restart_prompt']:
                input_user_msg = ChatMessage(
                    role_name=user_role_name,
                    role_type=RoleType.USER,
                    content=self.phase_state['restart_prompt']
                )
            self.reset_phase_state()

        # handle chats
        for i in range(chat_turn_limit):
            self.update_phase_state(current_turn=i + 1)
            assistant_response, user_response = role_play_session.step(input_user_msg, chat_turn_limit == 1)

            conversation_meta = "**" + assistant_role_name + "<->" + user_role_name + " on : " + str(
                phase_name) + ", turn " + str(i) + "**\n\n"

            if isinstance(assistant_response.msg, ChatMessage):
                log_visualize(role_play_session.assistant_agent.role_name,
                              conversation_meta + "[" + role_play_session.user_agent.system_message.content + "]\n\n" + assistant_response.msg.content)
                if role_play_session.assistant_agent.info:
                    seminar_conclusion = assistant_response.msg.content
                    self.update_phase_state(is_completed=True)
                    break
                if assistant_response.terminated:
                    self.update_phase_state(is_completed=True)
                    break

            if isinstance(user_response.msg, ChatMessage):
                log_visualize(role_play_session.user_agent.role_name,
                              conversation_meta + "[" + role_play_session.assistant_agent.system_message.content + "]\n\n" + user_response.msg.content)
                if role_play_session.user_agent.info:
                    seminar_conclusion = user_response.msg.content
                    self.update_phase_state(is_completed=True)
                    break
                if user_response.terminated:
                    self.update_phase_state(is_completed=True)
                    break

            if chat_turn_limit > 1 and isinstance(user_response.msg, ChatMessage):
                input_user_msg = user_response.msg
            else:
                break

        # conduct self reflection
        if need_reflect:
            if seminar_conclusion in [None, ""]:
                seminar_conclusion = "<INFO> " + self.self_reflection(task_prompt, role_play_session, phase_name,
                                                                      chat_env)
            if "recruiting" in phase_name:
                if "Yes".lower() not in seminar_conclusion.lower() and "No".lower() not in seminar_conclusion.lower():
                    seminar_conclusion = "<INFO> " + self.self_reflection(task_prompt, role_play_session,
                                                                          phase_name,
                                                                          chat_env)
            elif seminar_conclusion in [None, ""]:
                seminar_conclusion = "<INFO> " + self.self_reflection(task_prompt, role_play_session, phase_name,
                                                                      chat_env)
        else:
            seminar_conclusion = assistant_response.msg.content

        log_visualize("**[Seminar Conclusion]**:\n\n {}".format(seminar_conclusion))
        seminar_conclusion = seminar_conclusion.split("<INFO>")[-1]

        # 更新阶段状态
        self.update_phase_state(
            is_completed=True,
            seminar_conclusion=seminar_conclusion
        )
        return seminar_conclusion

    def self_reflection(self,
                        task_prompt: str,
                        role_play_session: RolePlaying,
                        phase_name: str,
                        chat_env: ChatEnv) -> str:
        """

        Args:
            task_prompt: user query prompt for building the software
            role_play_session: role play session from the chat phase which needs reflection
            phase_name: name of the chat phase which needs reflection
            chat_env: global chatchain environment

        Returns:
            reflected_content: str, reflected results

        """
        messages = role_play_session.assistant_agent.stored_messages if len(
            role_play_session.assistant_agent.stored_messages) >= len(
            role_play_session.user_agent.stored_messages) else role_play_session.user_agent.stored_messages
        messages = ["{}: {}".format(message.role_name, message.content.replace("\n\n", "\n")) for message in messages]
        messages = "\n\n".join(messages)

        if "recruiting" in phase_name:
            question = """Answer their final discussed conclusion (Yes or No) in the discussion without any other words, e.g., "Yes" """
        elif phase_name == "DemandAnalysis":
            question = """Answer their final product modality in the discussion without any other words, e.g., "PowerPoint" """
        elif phase_name == "LanguageChoose":
            question = """Conclude the programming language being discussed for software development, in the format: "*" where '*' represents a programming language." """
        elif phase_name == "EnvironmentDoc":
            question = """According to the codes and file format listed above, write a requirements.txt file to specify the dependencies or packages required for the project to run properly." """
        else:
            raise ValueError(f"Reflection of phase {phase_name}: Not Assigned.")

        # 确保 reflection_prompt 不为 None
        if self.reflection_prompt is None:
            self.reflection_prompt = """You are a counselor. You need to help the CEO to make a decision based on the following conversations between the CEO and other roles.
Here are the conversations:
{conversations}

{question}"""

        # Reflections actually is a special phase between CEO and counselor
        # They read the whole chatting history of this phase and give refined conclusion of this phase
        reflected_content = \
            self.chatting(chat_env=chat_env,
                          task_prompt=task_prompt,
                          assistant_role_name="Chief Executive Officer",
                          user_role_name="Counselor",
                          phase_prompt=self.reflection_prompt,
                          phase_name="Reflection",
                          assistant_role_prompt=self.ceo_prompt,
                          user_role_prompt=self.counselor_prompt,
                          placeholders={"conversations": messages, "question": question},
                          need_reflect=False,
                          memory=chat_env.memory,
                          chat_turn_limit=1,
                          model_type=self.model_type)

        if "recruiting" in phase_name:
            if "Yes".lower() in reflected_content.lower():
                return "Yes"
            return "No"
        else:
            return reflected_content

    @abstractmethod
    def update_phase_env(self, chat_env):
        """
        update self.phase_env (if needed) using chat_env, then the chatting will use self.phase_env to follow the context and fill placeholders in phase prompt
        must be implemented in customized phase
        the usual format is just like:
        ```
            self.phase_env.update({key:chat_env[key]})
        ```
        Args:
            chat_env: global chat chain environment

        Returns: None

        """
        pass

    @abstractmethod
    def update_chat_env(self, chat_env) -> ChatEnv:
        """
        update chan_env based on the results of self.execute, which is self.seminar_conclusion
        must be implemented in customized phase
        the usual format is just like:
        ```
            chat_env.xxx = some_func_for_postprocess(self.seminar_conclusion)
        ```
        Args:
            chat_env:global chat chain environment

        Returns:
            chat_env: updated global chat chain environment

        """
        pass

    def execute(self, chat_env, chat_turn_limit, need_reflect) -> ChatEnv:
        """
        execute the chatting in this phase
        1. receive information from environment: update the phase environment from global environment
        2. execute the chatting
        3. change the environment: update the global environment using the conclusion
        Args:
            chat_env: global chat chain environment
            chat_turn_limit: turn limit in each chat
            need_reflect: flag for reflection

        Returns:
            chat_env: updated global chat chain environment using the conclusion from this phase execution

        """
        self.update_phase_env(chat_env)
        print(f"chatting初始化时的phase_name：{self.phase_name}")
        self.seminar_conclusion = \
            self.chatting(chat_env=chat_env,
                          task_prompt=chat_env.env_dict['task_prompt'],
                          need_reflect=need_reflect,
                          assistant_role_name=self.assistant_role_name,
                          user_role_name=self.user_role_name,
                          phase_prompt=self.phase_prompt,
                          phase_name=self.phase_name,
                          assistant_role_prompt=self.assistant_role_prompt,
                          user_role_prompt=self.user_role_prompt,
                          chat_turn_limit=chat_turn_limit,
                          placeholders=self.phase_env,
                          memory=chat_env.memory,
                          model_type=self.model_type)
        # TODO 阶段用户控制功能：
        #  在 chatting 函数结束后，返回阶段结论，前端显示后，用户通过 API 发送下一步操作（继续或重新执行,重新执行可以添加prompt）。
        #  后端需要保存当前阶段的状态，比如任务提示、角色设置等，以便重新执行时使用。
        #  可能需要在会话中存储当前阶段的信息，或者在数据库中记录阶段状态。
        # 获取阶段结论
        print(f"\n阶段 {self.phase_name} 的结论：")
        print("-" * 50)
        print(self.seminar_conclusion)
        print("-" * 50)

        # 用户交互
        while True:
            user_input = input("\n请选择操作：\n1. 继续下一个阶段\n2. 修改当前阶段\n3. 查看文档\n请输入选项（1/2/3）：")
            if user_input == "1":
                break
            elif user_input == "2":
                modification = input("请输入修改建议：")
                # 更新阶段环境
                self.phase_env["modification_prompt"] = modification
                # 重新执行阶段
                self.seminar_conclusion = \
                    self.chatting(chat_env=chat_env,
                                  task_prompt=chat_env.env_dict['task_prompt'],
                                  need_reflect=need_reflect,
                                  assistant_role_name=self.assistant_role_name,
                                  user_role_name=self.user_role_name,
                                  phase_prompt=self.phase_prompt,
                                  phase_name=self.phase_name,
                                  assistant_role_prompt=self.assistant_role_prompt,
                                  user_role_prompt=self.user_role_prompt,
                                  chat_turn_limit=chat_turn_limit,
                                  placeholders=self.phase_env,
                                  memory=chat_env.memory,
                                  model_type=self.model_type)
                # 显示新的结论
                print(f"\n修改后的结论：")
                print("-" * 50)
                print(self.seminar_conclusion)
                print("-" * 50)
            elif user_input == "3":
                # 生成文档
                phase_data = {
                    'phase_name': self.phase_name,
                    'task_prompt': self.chat_env.env_dict['task_prompt'],
                    'phase_conclusion': self.seminar_conclusion,
                    'role_settings': json.dumps(self.phase_env)
                }
                document = generate_document(phase_data)
                doc_path = os.path.join(self.chat_env.env_dict['directory'], f"{self.phase_name}_documentation.md")
                with open(doc_path, "w", encoding="utf-8") as f:
                    f.write(document)
                print(f"\n文档已生成：{doc_path}")
            else:
                print("无效的选项，请重新输入")

        chat_env = self.update_chat_env(chat_env)

        # TODO 结论持久化：在 chatting 函数生成 seminar_conclusion 后，调用数据库操作函数，将结论和阶段信息存入 MySQL。
        #  需要设计数据库表结构，包含阶段名称、结论内容、时间戳等字段。使用 SQLAlchemy 等 ORM 工具来处理数据库操作。
        # 存储到数据库
        # 生成 seminar_conclusion 后，调用 save_phase_conclusion
        connection = create_connection()  # 之前定义的创建连接函数
        if connection:
            # 假设 self.memory 是 Memory 类实例，获取 AllMemory 实例
            chat_env.memory.upload()
            all_memory = chat_env.memory.memory_data.get("All")
            # if all_memory:
            # TODO 根据phase判断是text还是code
            # if self.phase_name in ["Programming", ...]
            # content_type="code"
            # else : content_type="text"
            self.save_phase_conclusion(
                connection=connection,
                content=self.seminar_conclusion,
                content_type="text",  # 可根据实际内容类型调整，比如是代码就传 "code"
                memory=all_memory,
            )
            print(f"调用save_phase_conclusion函数，phase_name：{self.phase_name}，role：{self.user_role_name}<->{self.assistant_role_name}，content：{self.seminar_conclusion}")
            close_connection(connection)  # 关闭数据库连接

        return chat_env

    def save_phase_conclusion(self,
                              connection: mysql.connector.connection.MySQLConnection,
                              content: str,
                              content_type: str,
                              memory: MemoryBase,  # 传入 MemoryBase 实例，利用其嵌入能力
                              phase_id: int = None
    ) -> None:
        """
                存储阶段结论到 conclusion 表，关联 phase 表，利用 Memory 模块生成嵌入向量
                :param connection: MySQL 数据库连接对象
                :param content: 结论内容（支持代码段）
                :param content_type: 内容类型，如 'text'/'code'
                :param memory: MemoryBase 子类实例，用于生成嵌入向量
                :param phase_id: 阶段 ID
                """
        # 先处理 phase 表相关，确保有对应的 phase 记录
        phase_cursor = connection.cursor()
        if phase_id is None:
            # 查询 phase 表是否已有该阶段名称的记录
            query_phase_sql = "SELECT phase_id FROM phase WHERE phase_name = %s"
            phase_cursor.execute(query_phase_sql, (self.phase_name,))
            result = phase_cursor.fetchone()
            if result:
                phase_id = result[0]
            else:
                # 插入新的 phase 记录
                insert_phase_sql = """
                            INSERT INTO phase (phase_name, phase_prompt) 
                            VALUES (%s, %s)
                        """
                phase_prompt = self.phase_prompt
                # 执行插入，数据库会自动为 phase_id 分配自增值
                phase_cursor.execute(insert_phase_sql, (self.phase_name, phase_prompt))
                connection.commit()
                phase_id = phase_cursor.lastrowid
        phase_cursor.close()

        # 生成嵌入向量，利用 Memory 模块里的 OpenAIEmbedding 能力
        embedding: List[float] = []
        if content_type == "text":
            embedding = memory.embedding_method.get_text_embedding(content)
        elif content_type == "code":
            embedding = memory.embedding_method.get_code_embedding(content)

        # 存储到 conclusion 表
        sql = """
                INSERT INTO conclusion (phase_id, role, content, content_type, embedding)
                VALUES (%s, %s, %s, %s, %s)
                """
        # embedding_json = json.dumps(embedding)
        # 改进：使用 MySQL 的 JSON_ARRAY 函数处理数组
        # 将 embedding 转换为 MySQL 可识别的 JSON 数组格式
        embedding_json_array = f"[{', '.join(map(str, embedding))}]"
        cursor = connection.cursor()
        try:
            # 使用 JSON_ARRAY_PACK 函数确保正确存储为 JSON 数组
            cursor.execute(sql,
                           (phase_id,
                            f"{self.user_role_name}<->{self.assistant_role_name}",
                            content,
                            content_type,
                            embedding_json_array # 传递格式化后的 JSON 数组字符串
                            ))
            connection.commit()
            print(f"成功存储结论，ID: {cursor.lastrowid}")
        except Error as e:
            connection.rollback()
            print(f"存储失败: {e}")
            # 打印详细的错误信息，帮助调试
            print(f"SQL: {sql}")
            print(
                f"参数: {phase_id}, {self.user_role_name}<->{self.assistant_role_name}, {content_type}, {embedding_json_array[:50]}...")
        finally:
            cursor.close()

class DemandAnalysis(Phase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, chat_env):
        pass

    def update_chat_env(self, chat_env) -> ChatEnv:
        if len(self.seminar_conclusion) > 0:
            chat_env.env_dict['modality'] = self.seminar_conclusion.split("<INFO>")[-1].lower().replace(".", "").strip()
        return chat_env


class LanguageChoose(Phase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, chat_env):
        self.phase_env.update({"task": chat_env.env_dict['task_prompt'],
                               "description": chat_env.env_dict['task_description'],
                               "modality": chat_env.env_dict['modality'],
                               "ideas": chat_env.env_dict['ideas']})

    def update_chat_env(self, chat_env) -> ChatEnv:
        if len(self.seminar_conclusion) > 0 and "<INFO>" in self.seminar_conclusion:
            chat_env.env_dict['language'] = self.seminar_conclusion.split("<INFO>")[-1].lower().replace(".", "").strip()
        elif len(self.seminar_conclusion) > 0:
            chat_env.env_dict['language'] = self.seminar_conclusion
        else:
            chat_env.env_dict['language'] = "Python"
        return chat_env


class Coding(Phase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, chat_env):
        gui = "" if not chat_env.config.gui_design \
            else "The software should be equipped with graphical user interface (GUI) so that user can visually and graphically use it; so you must choose a GUI framework (e.g., in Python, you can implement GUI via tkinter, Pygame, Flexx, PyGUI, etc,)."
        self.phase_env.update({"task": chat_env.env_dict['task_prompt'],
                               "description": chat_env.env_dict['task_description'],
                               "modality": chat_env.env_dict['modality'],
                               "ideas": chat_env.env_dict['ideas'],
                               "language": chat_env.env_dict['language'],
                               "gui": gui})

    def update_chat_env(self, chat_env) -> ChatEnv:
        chat_env.update_codes(self.seminar_conclusion)
        if len(chat_env.codes.codebooks.keys()) == 0:
            raise ValueError("No Valid Codes.")
        chat_env.rewrite_codes("Finish Coding")
        log_visualize(
            "**[Software Info]**:\n\n {}".format(get_info(chat_env.env_dict['directory'], self.log_filepath)))
        return chat_env


class ArtDesign(Phase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, chat_env):
        self.phase_env = {"task": chat_env.env_dict['task_prompt'],
                          "description": chat_env.env_dict['task_description'],
                          "language": chat_env.env_dict['language'],
                          "codes": chat_env.get_codes()}

    def update_chat_env(self, chat_env) -> ChatEnv:
        chat_env.proposed_images = chat_env.get_proposed_images_from_message(self.seminar_conclusion)
        log_visualize(
            "**[Software Info]**:\n\n {}".format(get_info(chat_env.env_dict['directory'], self.log_filepath)))
        return chat_env


class ArtIntegration(Phase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, chat_env):
        self.phase_env = {"task": chat_env.env_dict['task_prompt'],
                          "language": chat_env.env_dict['language'],
                          "codes": chat_env.get_codes(),
                          "images": "\n".join(
                              ["{}: {}".format(filename, chat_env.proposed_images[filename]) for
                               filename in sorted(list(chat_env.proposed_images.keys()))])}

    def update_chat_env(self, chat_env) -> ChatEnv:
        chat_env.update_codes(self.seminar_conclusion)
        chat_env.rewrite_codes("Finish Art Integration")
        # chat_env.generate_images_from_codes()
        log_visualize(
            "**[Software Info]**:\n\n {}".format(get_info(chat_env.env_dict['directory'], self.log_filepath)))
        return chat_env


class CodeComplete(Phase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, chat_env):
        self.phase_env.update({"task": chat_env.env_dict['task_prompt'],
                               "modality": chat_env.env_dict['modality'],
                               "ideas": chat_env.env_dict['ideas'],
                               "language": chat_env.env_dict['language'],
                               "codes": chat_env.get_codes(),
                               "unimplemented_file": ""})
        unimplemented_file = ""
        for filename in self.phase_env['pyfiles']:
            code_content = open(os.path.join(chat_env.env_dict['directory'], filename)).read()
            lines = [line.strip() for line in code_content.split("\n") if line.strip() == "pass"]
            if len(lines) > 0 and self.phase_env['num_tried'][filename] < self.phase_env['max_num_implement']:
                unimplemented_file = filename
                break
        self.phase_env['num_tried'][unimplemented_file] += 1
        self.phase_env['unimplemented_file'] = unimplemented_file

    def update_chat_env(self, chat_env) -> ChatEnv:
        chat_env.update_codes(self.seminar_conclusion)
        if len(chat_env.codes.codebooks.keys()) == 0:
            raise ValueError("No Valid Codes.")
        chat_env.rewrite_codes("Code Complete #" + str(self.phase_env["cycle_index"]) + " Finished")
        log_visualize(
            "**[Software Info]**:\n\n {}".format(get_info(chat_env.env_dict['directory'], self.log_filepath)))
        return chat_env


class CodeReviewComment(Phase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, chat_env):
        self.phase_env.update(
            {"task": chat_env.env_dict['task_prompt'],
             "modality": chat_env.env_dict['modality'],
             "ideas": chat_env.env_dict['ideas'],
             "language": chat_env.env_dict['language'],
             "codes": chat_env.get_codes(),
             "images": ", ".join(chat_env.incorporated_images)})

    def update_chat_env(self, chat_env) -> ChatEnv:
        chat_env.env_dict['review_comments'] = self.seminar_conclusion
        return chat_env


class CodeReviewModification(Phase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, chat_env):
        self.phase_env.update({"task": chat_env.env_dict['task_prompt'],
                               "modality": chat_env.env_dict['modality'],
                               "ideas": chat_env.env_dict['ideas'],
                               "language": chat_env.env_dict['language'],
                               "codes": chat_env.get_codes(),
                               "comments": chat_env.env_dict['review_comments']})

    def update_chat_env(self, chat_env) -> ChatEnv:
        if "```".lower() in self.seminar_conclusion.lower():
            chat_env.update_codes(self.seminar_conclusion)
            chat_env.rewrite_codes("Review #" + str(self.phase_env["cycle_index"]) + " Finished")
            log_visualize(
                "**[Software Info]**:\n\n {}".format(get_info(chat_env.env_dict['directory'], self.log_filepath)))
        self.phase_env['modification_conclusion'] = self.seminar_conclusion
        return chat_env


class CodeReviewHuman(Phase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, chat_env):
        self.phase_env.update({"task": chat_env.env_dict['task_prompt'],
                               "modality": chat_env.env_dict['modality'],
                               "ideas": chat_env.env_dict['ideas'],
                               "language": chat_env.env_dict['language'],
                               "codes": chat_env.get_codes()})

    def update_chat_env(self, chat_env) -> ChatEnv:
        if "```".lower() in self.seminar_conclusion.lower():
            chat_env.update_codes(self.seminar_conclusion)
            chat_env.rewrite_codes("Human Review #" + str(self.phase_env["cycle_index"]) + " Finished")
            log_visualize(
                "**[Software Info]**:\n\n {}".format(get_info(chat_env.env_dict['directory'], self.log_filepath)))
        return chat_env

    def execute(self, chat_env, chat_turn_limit, need_reflect) -> ChatEnv:
        self.update_phase_env(chat_env)
        log_visualize(
            f"**[Human-Agent-Interaction]**\n\n"
            f"Now you can participate in the development of the software!\n"
            f"The task is:  {chat_env.env_dict['task_prompt']}\n"
            f"Please input your feedback (in multiple lines). It can be bug report or new feature requirement.\n"
            f"You are currently in the #{self.phase_env['cycle_index']} human feedback with a total of {self.phase_env['cycle_num']} feedbacks\n"
            f"Type 'end' on a separate line to submit.\n"
            f"You can type \"Exit\" to quit this mode at any time.\n"
        )
        provided_comments = []
        while True:
            user_input = input(">>>>>>")
            if user_input.strip().lower() == "end":
                break
            if user_input.strip().lower() == "exit":
                provided_comments = ["exit"]
                break
            provided_comments.append(user_input)
        self.phase_env["comments"] = '\n'.join(provided_comments)
        log_visualize(
            f"**[User Provided Comments]**\n\n In the #{self.phase_env['cycle_index']} of total {self.phase_env['cycle_num']} comments: \n\n" +
            self.phase_env["comments"])
        if self.phase_env["comments"].strip().lower() == "exit":
            return chat_env

        self.seminar_conclusion = \
            self.chatting(chat_env=chat_env,
                          task_prompt=chat_env.env_dict['task_prompt'],
                          need_reflect=need_reflect,
                          assistant_role_name=self.assistant_role_name,
                          user_role_name=self.user_role_name,
                          phase_prompt=self.phase_prompt,
                          phase_name=self.phase_name,
                          assistant_role_prompt=self.assistant_role_prompt,
                          user_role_prompt=self.user_role_prompt,
                          chat_turn_limit=chat_turn_limit,
                          placeholders=self.phase_env,
                          memory=chat_env.memory,
                          model_type=self.model_type)
        chat_env = self.update_chat_env(chat_env)
        return chat_env

class TestErrorSummary(Phase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, chat_env):
        chat_env.generate_images_from_codes()
        (exist_bugs_flag, test_reports) = chat_env.exist_bugs()
        self.phase_env.update({"task": chat_env.env_dict['task_prompt'],
                               "modality": chat_env.env_dict['modality'],
                               "ideas": chat_env.env_dict['ideas'],
                               "language": chat_env.env_dict['language'],
                               "codes": chat_env.get_codes(),
                               "test_reports": test_reports,
                               "exist_bugs_flag": exist_bugs_flag})
        log_visualize("**[Test Reports]**:\n\n{}".format(test_reports))

    def update_chat_env(self, chat_env) -> ChatEnv:
        chat_env.env_dict['error_summary'] = self.seminar_conclusion
        chat_env.env_dict['test_reports'] = self.phase_env['test_reports']

        return chat_env

    def execute(self, chat_env, chat_turn_limit, need_reflect) -> ChatEnv:
        self.update_phase_env(chat_env)
        if "ModuleNotFoundError" in self.phase_env['test_reports']:
            chat_env.fix_module_not_found_error(self.phase_env['test_reports'])
            log_visualize(
                f"Software Test Engineer found ModuleNotFoundError:\n{self.phase_env['test_reports']}\n")
            pip_install_content = ""
            for match in re.finditer(r"No module named '(\S+)'", self.phase_env['test_reports'], re.DOTALL):
                module = match.group(1)
                pip_install_content += "{}\n```{}\n{}\n```\n".format("cmd", "bash", f"pip install {module}")
                log_visualize(f"Programmer resolve ModuleNotFoundError by:\n{pip_install_content}\n")
            self.seminar_conclusion = "nothing need to do"
        else:
            self.seminar_conclusion = \
                self.chatting(chat_env=chat_env,
                              task_prompt=chat_env.env_dict['task_prompt'],
                              need_reflect=need_reflect,
                              assistant_role_name=self.assistant_role_name,
                              user_role_name=self.user_role_name,
                              phase_prompt=self.phase_prompt,
                              phase_name=self.phase_name,
                              assistant_role_prompt=self.assistant_role_prompt,
                              user_role_prompt=self.user_role_prompt,
                              memory=chat_env.memory,
                              chat_turn_limit=chat_turn_limit,
                              placeholders=self.phase_env,
                              model_type=self.model_type)
        chat_env = self.update_chat_env(chat_env)
        return chat_env


class TestModification(Phase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, chat_env):
        self.phase_env.update({"task": chat_env.env_dict['task_prompt'],
                               "modality": chat_env.env_dict['modality'],
                               "ideas": chat_env.env_dict['ideas'],
                               "language": chat_env.env_dict['language'],
                               "test_reports": chat_env.env_dict['test_reports'],
                               "error_summary": chat_env.env_dict['error_summary'],
                               "codes": chat_env.get_codes()
                               })

    def update_chat_env(self, chat_env) -> ChatEnv:
        if "```".lower() in self.seminar_conclusion.lower():
            chat_env.update_codes(self.seminar_conclusion)
            chat_env.rewrite_codes("Test #" + str(self.phase_env["cycle_index"]) + " Finished")
            log_visualize(
                "**[Software Info]**:\n\n {}".format(get_info(chat_env.env_dict['directory'], self.log_filepath)))
        return chat_env


class EnvironmentDoc(Phase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, chat_env):
        self.phase_env.update({"task": chat_env.env_dict['task_prompt'],
                               "modality": chat_env.env_dict['modality'],
                               "ideas": chat_env.env_dict['ideas'],
                               "language": chat_env.env_dict['language'],
                               "codes": chat_env.get_codes()})

    def update_chat_env(self, chat_env) -> ChatEnv:
        chat_env._update_requirements(self.seminar_conclusion)
        chat_env.rewrite_requirements()
        log_visualize(
            "**[Software Info]**:\n\n {}".format(get_info(chat_env.env_dict['directory'], self.log_filepath)))
        return chat_env


class Manual(Phase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def update_phase_env(self, chat_env):
        self.phase_env.update({"task": chat_env.env_dict['task_prompt'],
                               "modality": chat_env.env_dict['modality'],
                               "ideas": chat_env.env_dict['ideas'],
                               "language": chat_env.env_dict['language'],
                               "codes": chat_env.get_codes(),
                               "requirements": chat_env.get_requirements()})

    def update_chat_env(self, chat_env) -> ChatEnv:
        chat_env._update_manuals(self.seminar_conclusion)
        chat_env.rewrite_manuals()
        return chat_env
