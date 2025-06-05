import pymysql
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def add_document_version_table():
    """添加文档版本表"""
    try:
        # 连接数据库
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='gwh0417##',
            database='chatdev'
        )
        
        with connection.cursor() as cursor:
            # 检查表是否存在
            cursor.execute("SHOW TABLES LIKE 'document_version'")
            if not cursor.fetchone():
                # 创建文档版本表
                cursor.execute("""
                    CREATE TABLE document_version (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        seminar_id INT NOT NULL,
                        phase_name VARCHAR(50) NOT NULL,
                        version INT NOT NULL,
                        document TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_seminar_phase (seminar_id, phase_name)
                    )
                """)
                print("成功创建文档版本表")
            else:
                print("文档版本表已存在")
                
        # 提交更改
        connection.commit()
        print("数据库更新完成")
        
    except Exception as e:
        print(f"错误: {str(e)}")
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    add_document_version_table() 