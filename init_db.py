import sqlite3

def init_database():
    conn = sqlite3.connect('student.db')
    cursor = conn.cursor()
    
    # 用户表 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            student_id TEXT,
            name TEXT NOT NULL,
            class TEXT
        )
    ''')
    
    # 成绩表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_name TEXT NOT NULL,
            score REAL NOT NULL,
            semester TEXT NOT NULL,
            academic_year TEXT NOT NULL
        )
    ''')
    
    # 查询时间段表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS query_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # 添加默认用户 - 明文密码
    users = [
        ('admin', 'admin123', 'admin', None, '系统管理员', None),
        ('teacher', 'teacher123', 'teacher', None, '张老师', None),
        ('stu2024001', '2024001', 'student', '2024001', '张三', '计算机1班'),
        ('stu2024002', '2024002', 'student', '2024002', '李四', '计算机1班'),
        ('stu2024003', '2024003', 'student', '2024003', '王五', '计算机2班')
    ]
    
    for user in users:
        cursor.execute('INSERT OR IGNORE INTO users VALUES (NULL, ?, ?, ?, ?, ?, ?)', user)
    
    # 添加示例成绩
    grades = [
        ('2024001', 'Python程序设计', 85.5, '2024-春季', '2023-2024'),
        ('2024001', '数据库原理', 92.0, '2024-春季', '2023-2024'),
        ('2024002', 'Python程序设计', 78.0, '2024-春季', '2023-2024'),
        ('2024002', '数据库原理', 88.5, '2024-春季', '2023-2024'),
        ('2024003', 'Python程序设计', 95.0, '2024-春季', '2023-2024')
    ]
    
    for grade in grades:
        cursor.execute('INSERT OR IGNORE INTO grades VALUES (NULL, ?, ?, ?, ?, ?)', grade)
    
    # 设置默认查询时间段
    cursor.execute('''
        INSERT OR IGNORE INTO query_periods (start_date, end_date, is_active)
        VALUES (?, ?, ?)
    ''', ('2024-01-01 00:00:00', '2025-12-31 23:59:59', 1))
    
    conn.commit()
    conn.close()
    print("数据库初始化完成！")

if __name__ == '__main__':
    init_database()