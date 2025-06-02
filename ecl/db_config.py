import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "bclx233.",
    "database": "chatdev_db",
    "port": 3306
}

def create_connection():
    """创建数据库连接"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        print("成功连接到MySQL数据库")
    except Error as e:
        print(f"连接失败: {e}")
    return connection

def close_connection(connection):
    """关闭数据库连接"""
    if connection:
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