"""阶段状态管理模块"""

# 存储当前阶段的实例
_current_phase = None

def set_current_phase(phase):
    """设置当前活动的阶段实例"""
    global _current_phase
    _current_phase = phase

def get_current_phase():
    """获取当前活动的阶段实例"""
    return _current_phase 