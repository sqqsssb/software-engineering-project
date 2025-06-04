import pymysql
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def add_document_field():
    """添加 document 字段到 phase_state 表"""
    try:
        # 连接数据库
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='gwh0417##',
            database='chatdev'
        )
        
        with connection.cursor() as cursor:
            # 检查字段是否已存在
            cursor.execute("SHOW COLUMNS FROM phase_state LIKE 'document'")
            if not cursor.fetchone():
                # 添加 document 字段
                cursor.execute("""
                    ALTER TABLE phase_state 
                    ADD COLUMN document TEXT 
                    AFTER phase_conclusion
                """)
                print("成功添加 document 字段")
            else:
                print("document 字段已存在")
                
        # 提交更改
        connection.commit()
        print("数据库更新完成")
        
    except Exception as e:
        print(f"错误: {str(e)}")
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    add_document_field() 