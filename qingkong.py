import mysql.connector

def truncate_all_tables():
    """清空所有聊天相关的表"""
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1",
        database="chat"
    )
    cursor = db.cursor()
    
    tables = [
        'groups_list',
        'users',
        'user_sessions',
        'friends',
        'groups_member',
        'group_messages',
        'messages'
    ]
    
    try:
        # 禁用外键检查（避免外键约束导致无法清空）
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        for table in tables:
            try:
                cursor.execute(f"TRUNCATE TABLE {table}")
                print(f"✅ 已清空表: {table}")
            except Exception as e:
                print(f"❌ 清空表 {table} 失败: {e}")
        
        # 恢复外键检查
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        db.commit()
        print("🎉 所有表清空完成")
        
    except Exception as e:
        print(f"执行失败: {e}")
        db.rollback()
    finally:
        cursor.close()
        db.close()

# 使用示例
if __name__ == "__main__":
    truncate_all_tables()