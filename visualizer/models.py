from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class PhaseState(db.Model):
    """阶段状态模型"""
    __tablename__ = 'phase_state'
    
    id = db.Column(db.Integer, primary_key=True)
    seminar_id = db.Column(db.Integer, nullable=False)
    phase_name = db.Column(db.String(50), nullable=False)
    task_prompt = db.Column(db.Text)
    role_settings = db.Column(db.Text)
    phase_conclusion = db.Column(db.Text)
    document = db.Column(db.Text)  # 存储生成的文档
    is_completed = db.Column(db.Boolean, default=False)
    needs_restart = db.Column(db.Boolean, default=False)
    restart_prompt = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'seminar_id': self.seminar_id,
            'phase_name': self.phase_name,
            'task_prompt': self.task_prompt,
            'role_settings': self.role_settings,
            'phase_conclusion': self.phase_conclusion,
            'document': self.document,
            'is_completed': self.is_completed,
            'needs_restart': self.needs_restart,
            'restart_prompt': self.restart_prompt,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class DocumentVersion(db.Model):
    """文档版本模型"""
    __tablename__ = 'document_version'
    
    id = db.Column(db.Integer, primary_key=True)
    seminar_id = db.Column(db.Integer, nullable=False)
    phase_name = db.Column(db.String(50), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    document = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @classmethod
    def get_next_version(cls, seminar_id, phase_name):
        """获取下一个版本号"""
        last_version = cls.query.filter_by(
            seminar_id=seminar_id,
            phase_name=phase_name
        ).order_by(cls.version.desc()).first()
        
        return (last_version.version + 1) if last_version else 1
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'seminar_id': self.seminar_id,
            'phase_name': self.phase_name,
            'version': self.version,
            'document': self.document,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 