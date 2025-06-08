import mysql.connector
from mysql.connector import Error

def get_db_config():
    """获取数据库配置"""
    return {
        "host": "localhost",
        "user": "root",
        "password": "gwh0417##",
        "database": "chatdev",
        "port": 3306
    }

def create_connection():
    """创建数据库连接"""
    try:
        connection = mysql.connector.connect(**get_db_config())
        if connection.is_connected():
            print("成功连接到 MySQL 数据库")
            return connection
    except Error as e:
        print(f"连接数据库时出错: {e}")
        return None

def close_connection(connection):
    """关闭数据库连接"""
    if connection and connection.is_connected():
        connection.close()
        print("数据库连接已关闭")


if __name__ == "__main__":
    # 创建数据库连接
    conn = create_connection()

    # 如果连接成功，可以执行简单的查询来验证
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"MySQL服务器版本: {version[0]}")
            cursor.close()
        except Error as e:
            print(f"执行查询时出错: {e}")
        finally:
            # 确保无论如何都会关闭连接
            close_connection(conn)