from flask import Blueprint, jsonify, request, send_file
from .models import db, PhaseState, DocumentVersion
from datetime import datetime
import json
import os
import markdown
from io import BytesIO
from camel.agents.chat_agent import ChatAgent
from chatdev.phase_state import get_current_phase
from camel.messages import SystemMessage
from camel.typing import RoleType

api = Blueprint('api', __name__)

def retrieve_related_memories(phase_data):
    """使用ChatAgent检索相关记忆"""
    try:
        # 解析角色设置
        try:
            role_settings = json.loads(phase_data['role_settings'])
            role_info = ", ".join([f"{role}: {title}" for role, title in role_settings.items()])
        except:
            role_info = phase_data['role_settings']
        
        # 创建SystemMessage对象
        system_message = SystemMessage(
            role_name="Memory Retriever",
            role_type=RoleType.ASSISTANT,
            content=f"""你是一个专业的软件工程助手，负责检索与{phase_data['phase_name']}阶段相关的记忆。
            请根据以下信息检索相关记忆：
            - 阶段名称：{phase_data['phase_name']}
            - 角色信息：{role_info}
            - 任务描述：{phase_data['task_prompt']}
            - 阶段结论：{phase_data['phase_conclusion']}
            """
        )
        
        # 创建ChatAgent实例
        chat_agent = ChatAgent(system_message=system_message)
        
        # 构建检索提示
        prompt = f"""
        请检索与以下内容相关的记忆：
        阶段：{phase_data['phase_name']}
        角色：{role_info}
        任务：{phase_data['task_prompt']}
        结论：{phase_data['phase_conclusion']}
        """
        
        # 检索相关记忆
        memories = chat_agent.retrieve_memories(prompt)
        
        # 格式化记忆内容
        formatted_memories = []
        for memory in memories:
            formatted_memories.append({
                'content': memory.content,
                'relevance': memory.relevance,
                'timestamp': memory.timestamp
            })
            
        return formatted_memories
    except Exception as e:
        print(f"检索记忆时出错: {str(e)}")
        return []

def generate_document_with_memories(phase_data, memories):
    """根据阶段数据和检索到的记忆生成文档"""
    phase_name = phase_data['phase_name']
    task_prompt = phase_data['task_prompt']
    phase_conclusion = phase_data['phase_conclusion']
    role_settings = json.loads(phase_data['role_settings'])
    
    # 创建ChatAgent实例，添加system_message参数
    system_message = SystemMessage(
        role_name="Document Generator",
        role_type=RoleType.ASSISTANT,
        content=f"""你是一个专业的软件工程文档生成助手，负责生成{phase_name}阶段的文档。
        请根据提供的阶段信息、角色设置和相关记忆，生成专业的软件工程文档。
        """
    )
    chat_agent = ChatAgent(system_message=system_message)
    
    # 根据不同阶段构建不同的提示
    if phase_name == "需求分析":
        prompt = f"""
        请根据以下信息生成软件需求规格说明书(SRS)：
        
        1. 基本信息：
        - 任务描述：{task_prompt}
        - 分析结论：{phase_conclusion}
        - 参与角色：{format_roles(role_settings)}
        
        2. 相关记忆：
        {json.dumps(memories, ensure_ascii=False, indent=2)}
        
        请生成一个专业的软件需求规格说明书，包含以下章节：
        
        1. 引言
           - 目的
           - 范围
           - 术语定义
        
        2. 系统概述
           - 系统描述
           - 系统功能
           - 用户特征
        
        3. 功能需求
           - 功能描述
           - 用例分析
           - 用户故事
        
        4. 非功能需求
           - 性能需求
           - 安全需求
           - 可靠性需求
           - 可维护性需求
        
        5. 系统接口
           - 用户接口
           - 外部接口
        
        6. 其他需求
           - 数据需求
           - 约束条件
        
        7. 附录
           - 修订历史
           - 参考文档
        """
    elif phase_name == "系统设计":
        prompt = f"""
        请根据以下信息生成软件设计文档(SDD)：
        
        1. 基本信息：
        - 任务描述：{task_prompt}
        - 设计结论：{phase_conclusion}
        - 参与角色：{format_roles(role_settings)}
        
        2. 相关记忆：
        {json.dumps(memories, ensure_ascii=False, indent=2)}
        
        请生成一个专业的软件设计文档，包含以下章节：
        
        1. 引言
           - 目的
           - 范围
           - 术语定义
        
        2. 系统架构
           - 架构概述
           - 技术架构
           - 部署架构
        
        3. 详细设计
           - 模块设计
           - 接口设计
           - 数据设计
           - 安全设计
        
        4. 系统接口
           - 外部接口
           - 内部接口
           - API设计
        
        5. 数据设计
           - 数据模型
           - 数据流
           - 数据存储
        
        6. 安全设计
           - 认证授权
           - 数据安全
           - 通信安全
        
        7. 附录
           - 修订历史
           - 参考文档
        """
    elif phase_name == "编码实现":
        prompt = f"""
        请根据以下信息生成软件实现文档：
        
        1. 基本信息：
        - 任务描述：{task_prompt}
        - 实现结论：{phase_conclusion}
        - 参与角色：{format_roles(role_settings)}
        
        2. 相关记忆：
        {json.dumps(memories, ensure_ascii=False, indent=2)}
        
        请生成一个专业的软件实现文档，包含以下章节：
        
        1. 引言
           - 目的
           - 范围
           - 术语定义
        
        2. 开发环境
           - 开发工具
           - 运行环境
           - 依赖说明
        
        3. 实现细节
           - 代码结构
           - 核心算法
           - 关键实现
        
        4. 接口实现
           - API实现
           - 接口说明
           - 调用示例
        
        5. 测试说明
           - 单元测试
           - 集成测试
           - 测试用例
        
        6. 部署说明
           - 部署步骤
           - 配置说明
           - 注意事项
        
        7. 附录
           - 修订历史
           - 参考文档
        """
    elif phase_name == "测试验证":
        prompt = f"""
        请根据以下信息生成软件测试报告：
        
        1. 基本信息：
        - 任务描述：{task_prompt}
        - 测试结论：{phase_conclusion}
        - 参与角色：{format_roles(role_settings)}
        
        2. 相关记忆：
        {json.dumps(memories, ensure_ascii=False, indent=2)}
        
        请生成一个专业的软件测试报告，包含以下章节：
        
        1. 引言
           - 目的
           - 范围
           - 术语定义
        
        2. 测试概述
           - 测试目标
           - 测试范围
           - 测试环境
        
        3. 测试计划
           - 测试策略
           - 测试方法
           - 测试工具
        
        4. 测试执行
           - 功能测试
           - 性能测试
           - 安全测试
        
        5. 测试结果
           - 测试用例
           - 测试结果
           - 问题统计
        
        6. 问题跟踪
           - 问题描述
           - 解决方案
           - 验证结果
        
        7. 附录
           - 修订历史
           - 参考文档
        """
    else:
        # 默认使用通用文档模板
        prompt = f"""
        请根据以下信息生成{phase_name}阶段的软件工程文档：
        
        1. 基本信息：
        - 任务描述：{task_prompt}
        - 阶段结论：{phase_conclusion}
        - 参与角色：{format_roles(role_settings)}
        
        2. 相关记忆：
        {json.dumps(memories, ensure_ascii=False, indent=2)}
        
        请生成一个专业的软件工程文档，包含必要的章节和内容。
        """
    
    try:
        # 使用AI生成文档
        response = chat_agent.chat(prompt)
        
        # 解析AI响应
        if response and isinstance(response, str):
            return response
        else:
            # 如果AI生成失败，使用默认模板
            return generate_default_document(phase_data)
            
    except Exception as e:
        print(f"AI生成文档时出错: {str(e)}")
        # 出错时使用默认模板
        return generate_default_document(phase_data)

def generate_default_document(phase_data):
    """生成默认文档模板"""
    phase_name = phase_data['phase_name']
    task_prompt = phase_data['task_prompt']
    phase_conclusion = phase_data['phase_conclusion']
    role_settings = json.loads(phase_data['role_settings'])
    
    # 根据不同阶段生成不同格式的文档
    if phase_name == "需求分析":
        return f"""# 软件需求规格说明书 (SRS)

## 1. 引言
### 1.1 目的
本文档旨在详细说明{task_prompt}的功能需求和非功能需求。

### 1.2 范围
本文档适用于整个软件开发团队，包括开发人员、测试人员和项目管理人员。

### 1.3 术语定义
- SRS: 软件需求规格说明书
- UI: 用户界面
- API: 应用程序接口

## 2. 系统概述
### 2.1 系统描述
{task_prompt}

### 2.2 系统功能
{phase_conclusion}

### 2.3 用户特征
{format_roles(role_settings)}

## 3. 功能需求
### 3.1 功能描述
{phase_conclusion}

### 3.2 用例分析
- 主要用例
- 次要用例
- 异常处理

## 4. 非功能需求
### 4.1 性能需求
- 响应时间
- 并发用户数
- 系统吞吐量

### 4.2 安全需求
- 用户认证
- 数据加密
- 访问控制

### 4.3 可靠性需求
- 系统可用性
- 数据备份
- 故障恢复

### 4.4 可维护性需求
- 代码规范
- 文档要求
- 测试要求

## 5. 系统接口
### 5.1 用户接口
- 界面布局
- 操作流程
- 交互方式

### 5.2 外部接口
- 硬件接口
- 软件接口
- 通信接口

## 6. 其他需求
### 6.1 数据需求
- 数据格式
- 数据存储
- 数据迁移

### 6.2 约束条件
- 技术约束
- 业务约束
- 法律约束

## 7. 附录
### 7.1 修订历史
- 版本号：1.0
- 修订日期：{datetime.now().strftime('%Y-%m-%d')}
- 修订人：系统自动生成

### 7.2 参考文档
- 项目计划书
- 用户调研报告
- 技术规范文档
"""
    elif phase_name == "系统设计":
        return f"""# 软件设计文档 (SDD)

## 1. 引言
### 1.1 目的
本文档详细说明系统的设计架构和实现方案。

### 1.2 范围
本文档适用于开发团队和系统架构师。

### 1.3 术语定义
- SDD: 软件设计文档
- API: 应用程序接口
- DB: 数据库

## 2. 系统架构
### 2.1 架构概述
{phase_conclusion}

### 2.2 技术架构
- 前端技术栈
- 后端技术栈
- 数据库技术
- 中间件技术

### 2.3 部署架构
- 服务器配置
- 网络架构
- 负载均衡
- 容灾备份

## 3. 详细设计
### 3.1 模块设计
- 核心模块
- 功能模块
- 接口模块

### 3.2 接口设计
- 内部接口
- 外部接口
- API设计

### 3.3 数据设计
- 数据模型
- 数据流
- 数据存储

### 3.4 安全设计
- 认证授权
- 数据安全
- 通信安全

## 4. 系统接口
### 4.1 外部接口
- 用户接口
- 第三方接口
- 系统接口

### 4.2 内部接口
- 模块接口
- 服务接口
- 数据接口

### 4.3 API设计
- RESTful API
- 接口规范
- 错误处理

## 5. 数据设计
### 5.1 数据模型
- 实体关系
- 数据字典
- 数据约束

### 5.2 数据流
- 数据流向
- 数据处理
- 数据存储

### 5.3 数据存储
- 存储方案
- 备份策略
- 恢复机制

## 6. 安全设计
### 6.1 认证授权
- 用户认证
- 权限控制
- 角色管理

### 6.2 数据安全
- 数据加密
- 数据备份
- 数据恢复

### 6.3 通信安全
- 传输加密
- 协议安全
- 防攻击措施

## 7. 附录
### 7.1 修订历史
- 版本号：1.0
- 修订日期：{datetime.now().strftime('%Y-%m-%d')}
- 修订人：系统自动生成

### 7.2 参考文档
- 需求规格说明书
- 技术规范文档
- 架构设计指南
"""
    elif phase_name == "编码实现":
        return f"""# 软件实现文档

## 1. 引言
### 1.1 目的
本文档详细说明系统的实现细节和开发过程。

### 1.2 范围
本文档适用于开发团队和测试团队。

### 1.3 术语定义
- IDE: 集成开发环境
- API: 应用程序接口
- SDK: 软件开发工具包

## 2. 开发环境
### 2.1 开发工具
- 开发IDE
- 版本控制
- 构建工具

### 2.2 运行环境
- 操作系统
- 运行环境
- 依赖库

### 2.3 依赖说明
- 前端依赖
- 后端依赖
- 数据库依赖

## 3. 实现细节
### 3.1 代码结构
- 目录结构
- 文件组织
- 命名规范

### 3.2 核心算法
- 算法说明
- 实现细节
- 性能优化

### 3.3 关键实现
- 核心功能
- 难点解决
- 优化方案

## 4. 接口实现
### 4.1 API实现
- 接口定义
- 参数说明
- 返回值

### 4.2 接口说明
- 调用方式
- 错误处理
- 示例代码

### 4.3 调用示例
- 请求示例
- 响应示例
- 错误示例

## 5. 测试说明
### 5.1 单元测试
- 测试用例
- 测试结果
- 覆盖率

### 5.2 集成测试
- 测试场景
- 测试结果
- 问题记录

### 5.3 测试用例
- 功能测试
- 性能测试
- 安全测试

## 6. 部署说明
### 6.1 部署步骤
- 环境准备
- 部署流程
- 配置说明

### 6.2 配置说明
- 系统配置
- 环境变量
- 参数设置

### 6.3 注意事项
- 部署注意
- 运行注意
- 维护注意

## 7. 附录
### 7.1 修订历史
- 版本号：1.0
- 修订日期：{datetime.now().strftime('%Y-%m-%d')}
- 修订人：系统自动生成

### 7.2 参考文档
- 设计文档
- API文档
- 测试文档
"""
    elif phase_name == "测试验证":
        return f"""# 软件测试报告

## 1. 引言
### 1.1 目的
本文档详细说明系统的测试过程和结果。

### 1.2 范围
本文档适用于测试团队和项目管理人员。

### 1.3 术语定义
- SIT: 系统集成测试
- UAT: 用户验收测试
- BUG: 软件缺陷

## 2. 测试概述
### 2.1 测试目标
{task_prompt}

### 2.2 测试范围
- 功能测试
- 性能测试
- 安全测试

### 2.3 测试环境
- 硬件环境
- 软件环境
- 网络环境

## 3. 测试计划
### 3.1 测试策略
- 测试方法
- 测试工具
- 测试流程

### 3.2 测试方法
- 黑盒测试
- 白盒测试
- 灰盒测试

### 3.3 测试工具
- 功能测试工具
- 性能测试工具
- 安全测试工具

## 4. 测试执行
### 4.1 功能测试
- 测试用例
- 测试结果
- 问题记录

### 4.2 性能测试
- 测试指标
- 测试结果
- 性能分析

### 4.3 安全测试
- 安全测试项
- 测试结果
- 安全建议

## 5. 测试结果
### 5.1 测试用例
- 用例统计
- 执行结果
- 通过率

### 5.2 测试结果
{phase_conclusion}

### 5.3 问题统计
- 问题分类
- 问题等级
- 解决状态

## 6. 问题跟踪
### 6.1 问题描述
- 问题详情
- 复现步骤
- 影响范围

### 6.2 解决方案
- 解决措施
- 验证方法
- 预防措施

### 6.3 验证结果
- 验证过程
- 验证结果
- 遗留问题

## 7. 附录
### 7.1 修订历史
- 版本号：1.0
- 修订日期：{datetime.now().strftime('%Y-%m-%d')}
- 修订人：系统自动生成

### 7.2 参考文档
- 测试计划
- 测试用例
- 问题报告
"""
    else:
        # 默认文档模板
        return f"""# {phase_name}文档

## 1. 引言
### 1.1 目的
本文档详细说明{phase_name}阶段的工作内容和成果。

### 1.2 范围
本文档适用于项目相关人员和团队。

### 1.3 术语定义
- 相关术语定义

## 2. 工作内容
### 2.1 任务描述
{task_prompt}

### 2.2 工作成果
{phase_conclusion}

### 2.3 参与人员
{format_roles(role_settings)}

## 3. 详细说明
### 3.1 主要内容
- 内容1
- 内容2
- 内容3

### 3.2 关键点
- 关键点1
- 关键点2
- 关键点3

### 3.3 注意事项
- 注意1
- 注意2
- 注意3

## 4. 总结
### 4.1 成果总结
- 成果1
- 成果2
- 成果3

### 4.2 经验总结
- 经验1
- 经验2
- 经验3

### 4.3 后续建议
- 建议1
- 建议2
- 建议3

## 5. 附录
### 5.1 修订历史
- 版本号：1.0
- 修订日期：{datetime.now().strftime('%Y-%m-%d')}
- 修订人：系统自动生成

### 5.2 参考文档
- 文档1
- 文档2
- 文档3
"""

def generate_document(phase_data):
    """根据阶段数据生成软件文档"""
    # 检索相关记忆
    memories = retrieve_related_memories(phase_data)
    
    # 使用记忆生成文档
    return generate_document_with_memories(phase_data, memories)

def format_roles(role_settings):
    """格式化角色信息"""
    roles = []
    for role, title in role_settings.items():
        roles.append(f"- {title} ({role})")
    return "\n".join(roles)

@api.route('/seminar/<int:seminar_id>/phase/<phase_name>/document/export', methods=['GET'])
def export_document(seminar_id, phase_name):
    """导出文档"""
    try:
        phase = PhaseState.query.filter_by(
            seminar_id=seminar_id,
            phase_name=phase_name
        ).first()
        
        if not phase:
            return jsonify({
                'error': 'Phase not found',
                'message': f'No phase found for seminar {seminar_id} and phase {phase_name}'
            }), 404
            
        if not phase.document:
            return jsonify({
                'error': 'Document not found',
                'message': 'No document generated for this phase yet'
            }), 404
            
        # 创建内存文件
        output = BytesIO()
        output.write(phase.document.encode('utf-8'))
        output.seek(0)
        
        # 生成文件名
        filename = f"{phase_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        return send_file(
            output,
            mimetype='text/markdown',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api.route('/seminar/<int:seminar_id>/phase/<phase_name>/document/preview', methods=['GET'])
def preview_document(seminar_id, phase_name):
    """预览文档"""
    try:
        phase = PhaseState.query.filter_by(
            seminar_id=seminar_id,
            phase_name=phase_name
        ).first()
        
        if not phase:
            return jsonify({
                'error': 'Phase not found',
                'message': f'No phase found for seminar {seminar_id} and phase {phase_name}'
            }), 404
            
        if not phase.document:
            return jsonify({
                'error': 'Document not found',
                'message': 'No document generated for this phase yet'
            }), 404
            
        try:
            # 将Markdown转换为HTML
            html_content = markdown.markdown(
                phase.document,
                extensions=['extra', 'codehilite', 'tables']
            )
            
            return jsonify({
                'status': 'success',
                'data': {
                    'html': html_content,
                    'markdown': phase.document,
                    'generated_at': phase.updated_at.isoformat()
                }
            })
        except Exception as e:
            print(f"Markdown转换错误: {str(e)}")
            # 如果转换失败，返回原始Markdown
            return jsonify({
                'status': 'success',
                'data': {
                    'html': f"<pre>{phase.document}</pre>",
                    'markdown': phase.document,
                    'generated_at': phase.updated_at.isoformat()
                }
            })
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api.route('/seminar/<int:seminar_id>/phase/<phase_name>/document/versions', methods=['GET'])
def get_document_versions(seminar_id, phase_name):
    """获取文档版本历史"""
    try:
        versions = DocumentVersion.query.filter_by(
            seminar_id=seminar_id,
            phase_name=phase_name
        ).order_by(DocumentVersion.version.desc()).all()
        
        return jsonify({
            'status': 'success',
            'data': [version.to_dict() for version in versions]
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api.route('/seminar/<int:seminar_id>/phase/<phase_name>', methods=['GET'])
def get_phase_state(seminar_id, phase_name):
    """获取阶段状态"""
    try:
        phase = PhaseState.query.filter_by(
            seminar_id=seminar_id,
            phase_name=phase_name
        ).first()
        
        if not phase:
            return jsonify({
                'error': 'Phase not found',
                'message': f'No phase found for seminar {seminar_id} and phase {phase_name}'
            }), 404
            
        return jsonify({
            'status': 'success',
            'data': phase.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api.route('/seminar/<int:seminar_id>/phase/<phase_name>', methods=['POST'])
def update_phase_state(seminar_id, phase_name):
    """更新阶段状态"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'No data provided'
            }), 400
            
        phase = PhaseState.query.filter_by(
            seminar_id=seminar_id,
            phase_name=phase_name
        ).first()
        
        if not phase:
            # 创建新阶段
            phase = PhaseState(
                seminar_id=seminar_id,
                phase_name=phase_name
            )
            db.session.add(phase)
            
        # 更新字段
        for field in ['task_prompt', 'role_settings', 'phase_conclusion']:
            if field in data:
                setattr(phase, field, data[field])
                
        if 'is_completed' in data:
            phase.is_completed = bool(data['is_completed'])
            
        if 'needs_restart' in data:
            phase.needs_restart = bool(data['needs_restart'])
            
        if 'restart_prompt' in data:
            phase.restart_prompt = data['restart_prompt']
            
        db.session.commit()
        
        # 如果阶段完成，生成文档并保存版本
        if phase.is_completed:
            document = generate_document(phase.to_dict())
            phase.document = document
            
            # 创建新版本
            version = DocumentVersion(
                seminar_id=seminar_id,
                phase_name=phase_name,
                document=document,
                version=DocumentVersion.get_next_version(seminar_id, phase_name)
            )
            db.session.add(version)
            
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Phase state updated successfully',
            'data': phase.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api.route('/seminar/<int:seminar_id>/phase/<phase_name>/action', methods=['POST'])
def phase_action(seminar_id, phase_name):
    """处理阶段操作（继续/重新执行）"""
    try:
        data = request.get_json()
        if not data or 'action' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Action is required'
            }), 400
            
        action = data['action']
        if action not in ['continue', 'restart']:
            return jsonify({
                'error': 'Invalid action',
                'message': 'Action must be either "continue" or "restart"'
            }), 400
            
        phase = PhaseState.query.filter_by(
            seminar_id=seminar_id,
            phase_name=phase_name
        ).first()
        
        if not phase:
            return jsonify({
                'error': 'Phase not found',
                'message': f'No phase found for seminar {seminar_id} and phase {phase_name}'
            }), 404
            
        if action == 'continue':
            phase.is_completed = True
            phase.needs_restart = False
            phase.restart_prompt = None
            
            # 生成文档
            document = generate_document(phase.to_dict())
            phase.document = document
        else:  # restart
            phase.is_completed = False
            phase.needs_restart = True
            phase.restart_prompt = data.get('restart_prompt')
            phase.document = None  # 清除之前的文档
            
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Phase {action}ed successfully',
            'data': phase.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api.route('/seminar/<int:seminar_id>/phase/<phase_name>/document', methods=['GET'])
def get_phase_document(seminar_id, phase_name):
    """获取阶段文档"""
    try:
        phase = PhaseState.query.filter_by(
            seminar_id=seminar_id,
            phase_name=phase_name
        ).first()
        
        if not phase:
            return jsonify({
                'error': 'Phase not found',
                'message': f'No phase found for seminar {seminar_id} and phase {phase_name}'
            }), 404
            
        if not phase.document:
            return jsonify({
                'error': 'Document not found',
                'message': 'No document generated for this phase yet'
            }), 404
            
        return jsonify({
            'status': 'success',
            'data': {
                'document': phase.document,
                'generated_at': phase.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api.route('/seminar/<int:seminar_id>/phase/<phase_name>/chat', methods=['POST'])
def chatting(seminar_id, phase_name):
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Message is required'
            }), 400

        # 获取当前阶段
        phase = PhaseState.query.filter_by(
            seminar_id=seminar_id,
            phase_name=phase_name
        ).first()
        if not phase:
            return jsonify({
                'error': 'Phase not found',
                'message': f'No phase found for seminar {seminar_id} and phase {phase_name}'
            }), 404

        # 解析角色设置
        try:
            role_settings = json.loads(phase.role_settings)
            role_info = ", ".join([f"{role}: {title}" for role, title in role_settings.items()])
        except:
            role_info = phase.role_settings

        # 创建SystemMessage对象
        system_message = SystemMessage(
            role_name="Software Engineering Assistant",
            role_type=RoleType.ASSISTANT,
            content=f"""你是一个专业的软件工程助手，负责处理{phase_name}阶段的问题。
            请根据以下信息提供专业的建议和解答：
            - 阶段名称：{phase_name}
            - 角色信息：{role_info}
            - 任务描述：{phase.task_prompt}
            - 当前结论：{phase.phase_conclusion}
            """
        )
        
        # 创建ChatAgent实例
        chat_agent = ChatAgent(system_message=system_message)
        
        # 调用 ChatAgent 处理消息
        response = chat_agent.chat(data['message'])

        # 返回阶段结论
        conclusion = phase.phase_conclusion if phase.phase_conclusion else "暂无结论"

        return jsonify({
            'status': 'success',
            'data': {
                'response': response,
                'conclusion': conclusion
            }
        })

    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@api.route('/seminar/<int:seminar_id>/phase/<phase_name>/control', methods=['POST'])
def phase_control(seminar_id, phase_name):
    try:
        data = request.get_json()
        if not data or 'action' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Action is required'
            }), 400

        action = data['action']
        phase = PhaseState.query.filter_by(
            seminar_id=seminar_id,
            phase_name=phase_name
        ).first()
        if not phase:
            return jsonify({
                'error': 'Phase not found',
                'message': f'No phase found for seminar {seminar_id} and phase {phase_name}'
            }), 404

        if action == 'retrieve':
            # 用户不修改，检索相关记忆
            system_message = f"""你是一个专业的软件工程助手，负责检索与{phase_name}阶段相关的记忆。
            请根据阶段名称和角色设置检索相关的历史记录和结论。
            """
            chat_agent = ChatAgent(system_message=system_message)
            
            # 解析角色设置
            try:
                role_settings = json.loads(phase.role_settings)
                role_info = ", ".join([f"{role}: {title}" for role, title in role_settings.items()])
            except:
                role_info = phase.role_settings
            
            # 构建检索提示
            prompt = f"""
            请检索与以下内容相关的记忆：
            阶段：{phase_name}
            角色：{role_info}
            任务：{phase.task_prompt}
            结论：{phase.phase_conclusion}
            """
            
            memories = chat_agent.retrieve_memories(prompt)
            return jsonify({
                'status': 'success',
                'data': {
                    'memories': memories
                }
            })
        elif action == 'update':
            # 用户修改，更新结论
            if 'conclusion' not in data:
                return jsonify({
                    'error': 'Invalid request',
                    'message': 'Conclusion is required for update'
                }), 400
            phase.phase_conclusion = data['conclusion']
            db.session.commit()
            return jsonify({
                'status': 'success',
                'message': 'Phase conclusion updated successfully',
                'data': phase.to_dict()
            })
        else:
            return jsonify({
                'error': 'Invalid action',
                'message': 'Action must be either "retrieve" or "update"'
            }), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500 