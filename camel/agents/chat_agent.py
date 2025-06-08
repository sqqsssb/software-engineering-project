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
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
from mysql.connector import Error
from tenacity import retry
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential

from camel.agents import BaseAgent
from camel.configs import ChatGPTConfig
from camel.messages import ChatMessage, MessageType, SystemMessage
from camel.model_backend import ModelBackend, ModelFactory
from camel.typing import ModelType, RoleType
from camel.utils import (
    get_model_token_limit,
    num_tokens_from_messages,
    openai_api_key_required,
)
from chatdev.utils import log_visualize
from ecl.db_config import create_connection, close_connection
from ecl.embedding import OpenAIEmbedding

try:
    from openai.types.chat import ChatCompletion

    openai_new_api = True  # new openai api version
except ImportError:
    openai_new_api = False  # old openai api version


@dataclass(frozen=True)
class ChatAgentResponse:
    r"""Response of a ChatAgent.

    Attributes:
        msgs (List[ChatMessage]): A list of zero, one or several messages.
            If the list is empty, there is some error in message generation.
            If the list has one message, this is normal mode.
            If the list has several messages, this is the critic mode.
        terminated (bool): A boolean indicating whether the agent decided
            to terminate the chat session.
        info (Dict[str, Any]): Extra information about the chat message.
    """
    msgs: List[ChatMessage]
    terminated: bool
    info: Dict[str, Any]

    @property
    def msg(self):
        if self.terminated:
            raise RuntimeError("error in ChatAgentResponse, info:{}".format(str(self.info)))
        if len(self.msgs) > 1:
            raise RuntimeError("Property msg is only available for a single message in msgs")
        elif len(self.msgs) == 0:
            if len(self.info) > 0:
                raise RuntimeError("Empty msgs in ChatAgentResponse, info:{}".format(str(self.info)))
            else:
                # raise RuntimeError("Known issue that msgs is empty and there is no error info, to be fix")
                return None
        return self.msgs[0]


class ChatAgent(BaseAgent):
    r"""Class for managing conversations of CAMEL Chat Agents.

    Args:
        system_message (SystemMessage): The system message for the chat agent.
        with_memory(bool): The memory setting of the chat agent.
        model (ModelType, optional): The LLM model to use for generating
            responses. (default :obj:`ModelType.GPT_3_5_TURBO`)
        model_config (Any, optional): Configuration options for the LLM model.
            (default: :obj:`None`)
        message_window_size (int, optional): The maximum number of previous
            messages to include in the context window. If `None`, no windowing
            is performed. (default: :obj:`None`)
    """

    def __init__(
            self,
            system_message: SystemMessage,
            memory = None,
            model: Optional[ModelType] = None,
            model_config: Optional[Any] = None,
            message_window_size: Optional[int] = None,
            phase_name: str = "",  # 新增：当前阶段名称（用于过滤记忆）
            top_k: int = 5,  # 最多返回5条相似记忆
            similarity_threshold: float = 0.75  # 相似度阈值
    ) -> None:

        self.system_message: SystemMessage = system_message
        self.role_name: str = system_message.role_name
        self.role_type: RoleType = system_message.role_type
        self.model: ModelType = (model if model is not None else ModelType.GPT_4O_MINI)
        self.model_config: ChatGPTConfig = model_config or ChatGPTConfig()
        self.model_token_limit: int = get_model_token_limit(self.model)
        self.message_window_size: Optional[int] = message_window_size
        self.model_backend: ModelBackend = ModelFactory.create(self.model, self.model_config.__dict__)
        self.terminated: bool = False
        self.info: bool = False
        self.phase_name = phase_name
        print(f"进入ChatAgent初始化函数后的phase_name：{self.phase_name}")
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.embedding_method = OpenAIEmbedding()  # 向量生成器
        self.init_messages()
        if memory !=None and self.role_name in["Code Reviewer","Programmer","Software Test Engineer"]:
            self.memory = memory.memory_data.get("All")
        else:
            self.memory = None

    def reset(self) -> List[MessageType]:
        r"""Resets the :obj:`ChatAgent` to its initial state and returns the
        stored messages.

        Returns:
            List[MessageType]: The stored messages.
        """
        self.terminated = False
        self.init_messages()
        return self.stored_messages

    def get_info(
            self,
            id: Optional[str],
            usage: Optional[Dict[str, int]],
            termination_reasons: List[str],
            num_tokens: int,
    ) -> Dict[str, Any]:
        r"""Returns a dictionary containing information about the chat session.

        Args:
            id (str, optional): The ID of the chat session.
            usage (Dict[str, int], optional): Information about the usage of
                the LLM model.
            termination_reasons (List[str]): The reasons for the termination of
                the chat session.
            num_tokens (int): The number of tokens used in the chat session.

        Returns:
            Dict[str, Any]: The chat session information.
        """
        return {
            "id": id,
            "usage": usage,
            "termination_reasons": termination_reasons,
            "num_tokens": num_tokens,
        }

    def init_messages(self) -> None:
        r"""Initializes the stored messages list with the initial system
        message.
        """
        self.stored_messages: List[MessageType] = [self.system_message]

    def update_messages(self, message: ChatMessage) -> List[MessageType]:
        r"""Updates the stored messages list with a new message.

        Args:
            message (ChatMessage): The new message to add to the stored
                messages.

        Returns:
            List[ChatMessage]: The updated stored messages.
        """
        self.stored_messages.append(message)
        return self.stored_messages
    def use_memory(self,input_message) -> List[MessageType]:
        if self.memory is None :
            return None
        else:
            if self.role_name == "Programmer":
                result = self.memory.memory_retrieval(input_message,"code")
                if result != None:
                    target_memory,distances, mids,task_list,task_dir_list = result
                    if target_memory != None and len(target_memory) != 0:
                        target_memory="".join(target_memory)
                        #self.stored_messages[-1].content = self.stored_messages[-1].content+"Here is some code you've previously completed:"+target_memory+"You can refer to the previous script to complement this task."
                        log_visualize(self.role_name,
                                            "thinking back and found some related code: \n--------------------------\n"
                                            + target_memory)
                else:
                    target_memory = None
                    log_visualize(self.role_name,
                                         "thinking back but find nothing useful")

            else:
                result = self.memory.memory_retrieval(input_message, "text")
                if result != None:
                    target_memory, distances, mids, task_list, task_dir_list = result
                    if target_memory != None and len(target_memory) != 0:
                        target_memory=";".join(target_memory)
                        #self.stored_messages[-1].content = self.stored_messages[-1].content+"Here are some effective and efficient instructions you have sent to the assistant :"+target_memory+"You can refer to these previous excellent instructions to better instruct assistant here."
                        log_visualize(self.role_name,
                                            "thinking back and found some related text: \n--------------------------\n"
                                            + target_memory)
                else:
                    target_memory = None
                    log_visualize(self.role_name,
                                         "thinking back but find nothing useful")

        return target_memory

    def retrieve_memory(self, input_message: str) -> List[str]:
        """从数据库检索与输入消息相似的记忆"""
        # 1. 生成输入消息的向量
        input_embedding = self.embedding_method.get_text_embedding(input_message)

        print(f"输入向量维度: {len(input_embedding)}")
        print(f"输入向量示例: {input_embedding[:5]}...")

        # 2. 查询数据库：使用余弦相似度匹配（示例SQL，需根据实际表结构调整）
        connection = create_connection()  # 复用之前的数据库连接函数
        relevant_memory = []
        if connection:
            try:
                cursor = connection.cursor()
                # 简化 SQL，先捞取合法数据，再在 Python 侧计算相似度
                sql = """
                                SELECT conclusion_id, content, embedding
                                FROM conclusion
                                WHERE JSON_VALID(embedding) = 1
                                ORDER BY conclusion_id DESC  -- 按主键倒序，最新记录在前
                                LIMIT %s
                                """
                cursor.execute(sql, (self.top_k,))
                results = cursor.fetchall()

                input_vec = np.array(input_embedding, dtype=np.float32)
                for row in results:
                    conclusion_id, content, embedding_json = row
                    try:
                        embedding = np.array(json.loads(embedding_json), dtype=np.float32)
                        if embedding.shape != input_vec.shape:
                            continue
                        # 余弦相似度公式
                        similarity = np.dot(embedding, input_vec) / (
                                    np.linalg.norm(embedding) * np.linalg.norm(input_vec))
                        if similarity >= self.similarity_threshold:
                            relevant_memory.append(content)
                            print(f"在{self.phase_name}阶段，第{conclusion_id}条记录数据库查询相似度：{similarity}，大于等于阈值{self.similarity_threshold}")
                        else:
                            print(f"在{self.phase_name}阶段，第{conclusion_id}条记录数据库查询相似度：{similarity}，小于阈值{self.similarity_threshold}")
                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"解析/计算异常: {e}，跳过该条记录")

            except Error as e:
                print(f"记忆检索失败: {e}")
            finally:
                close_connection(connection)
        print(f"最终返回 {len(relevant_memory)} 条相关记忆")
        return relevant_memory

    # @retry(wait=wait_exponential(min=5, max=60), stop=stop_after_attempt(5))
    # @openai_api_key_required
    def step(
            self,
            input_message: ChatMessage,
    ) -> ChatAgentResponse:
        r"""Performs a single step in the chat session by generating a response
        to the input message.

        Args:
            input_message (ChatMessage): The input message to the agent.

        Returns:
            ChatAgentResponse: A struct
                containing the output messages, a boolean indicating whether
                the chat session has terminated, and information about the chat
                session.
        """

        # TODO 记忆检索：在 ChatAgent 的 step 方法中，处理输入消息前，先检索数据库中的相关记忆。
        #  比如，根据阶段名称和角色名称，查询之前的结论或代码，将其作为上下文加入到消息中。
        #  需要在 ChatAgent 中添加 memory 检索的逻辑，可能在 update_messages 或 step 方法中调用检索函数，并将结果添加到消息列表中。
        # 检索记忆数据库
        # memory_entries = search_memory(
        #     role_name=self.role_name,
        #     phase_name=current_phase_name  # 需从上下文中获取阶段名
        # )
        # # 将记忆添加到消息历史
        # for entry in memory_entries:
        #     self.update_messages(ChatMessage(content=entry.content))

        # 1. 检索相关记忆
        relevant_memory = self.retrieve_memory(input_message.content)

        # 2. 将记忆添加到对话历史（作为system prompt或user message）
        for memory_content in relevant_memory:
            # 示例：以System Message形式注入上下文
            memory_msg = ChatMessage(
                role_name="System",
                role="system",
                content=f"历史记忆：{memory_content}",
                meta_dict=dict(), role_type=None,
            )
            self.update_messages(memory_msg)
        print(f"ChatAgent的step函数中，relevant_memory = {relevant_memory}")

        # 3. 原有消息处理逻辑
        messages = self.update_messages(input_message)
        print(f"ChatAgent的step函数中，messages = (relevant_memory + input_message):{messages}")

        if self.message_window_size is not None and len(
                messages) > self.message_window_size:
            messages = [self.system_message
                        ] + messages[-self.message_window_size:]
        openai_messages = [message.to_openai_message() for message in messages]
        print(
            f"ChatAgent的step函数中，openai_messages = (relevant_memory + input_message).to_openai_message():{openai_messages}")
        num_tokens = num_tokens_from_messages(openai_messages, self.model)

        # for openai_message in openai_messages:
        #     # print("{}\t{}".format(openai_message.role, openai_message.content))
        #     print("{}\t{}\t{}".format(openai_message["role"], hash(openai_message["content"]), openai_message["content"][:60].replace("\n", "")))
        # print()

        output_messages: Optional[List[ChatMessage]]
        info: Dict[str, Any]

        if num_tokens < self.model_token_limit:
            response = self.model_backend.run(messages=openai_messages)

            if openai_new_api:
                if not isinstance(response, ChatCompletion):
                    raise RuntimeError("OpenAI returned unexpected struct")

                # 移除每个 choice.message 中的 'annotations' 键值对
                for choice in response.choices:
                    message_dict = dict(choice.message)
                    message_dict.pop('annotations', None)  # 使用 pop 方法移除 'annotations' 键值对，如果不存在则不报错
                    choice.message = message_dict  # 更新 choice.message
                print(response.choices[0].message)
                output_messages = [
                    ChatMessage(role_name=self.role_name, role_type=self.role_type,
                                meta_dict=dict(), **dict(choice.message))
                    for choice in response.choices
                ]

                info = self.get_info(
                    response.id,
                    response.usage,
                    [str(choice.finish_reason) for choice in response.choices],
                    num_tokens,
                )

            # TODO strict <INFO> check, only in the beginning of the line
            # if "<INFO>" in output_messages[0].content:
            if output_messages[0].content.split("\n")[-1].startswith("<INFO>"):
                self.info = True
        else:
            self.terminated = True
            output_messages = []

            info = self.get_info(
                None,
                None,
                ["max_tokens_exceeded_by_camel"],
                num_tokens,
            )

        return ChatAgentResponse(output_messages, self.terminated, info)

    def __repr__(self) -> str:
        r"""Returns a string representation of the :obj:`ChatAgent`.

        Returns:
            str: The string representation of the :obj:`ChatAgent`.
        """
        return f"ChatAgent({self.role_name}, {self.role_type}, {self.model})"

    def retrieve_memories(self, input_message: str) -> List[str]:
        """检索与当前阶段相关的记忆

        Args:
            input_message: 用户输入的消息

        Returns:
            List[str]: 检索到的记忆列表
        """
        try:
            # 获取数据库连接
            connection = create_connection()
            if not connection:
                return []

            cursor = connection.cursor(dictionary=True)

            # 构建查询 - 直接使用phase_name字段
            query = """
            SELECT content 
            FROM memories 
            WHERE phase_name = %s
            ORDER BY created_at DESC
            LIMIT %s
            """

            cursor.execute(query, (self.phase_name, self.top_k))
            memories = cursor.fetchall()

            # 关闭连接
            cursor.close()
            close_connection(connection)

            # 返回记忆内容
            return [memory['content'] for memory in memories]

        except Exception as e:
            print(f"检索记忆时出错: {str(e)}")
            return []

    def chat(self, input_message: str) -> str:
        """处理用户输入并生成响应

        Args:
            input_message: 用户输入的消息

        Returns:
            str: 生成的响应
        """
        try:
            # 检索相关记忆
            memories = self.retrieve_memories(input_message)

            # 构建提示
            prompt = f"""当前阶段: {self.phase_name}
相关记忆:
{memories}
用户输入: {input_message}"""

            # 构造消息列表
            messages = [
                {"role": "system", "content": self.system_message.content},
                {"role": "user", "content": prompt}
            ]

            # 生成响应
            response = self.model_backend.run(messages=messages)
            return response.choices[0].message.content

        except Exception as e:
            print(f"生成响应时出错: {str(e)}")
            return "抱歉，我遇到了一些问题，无法生成响应。"