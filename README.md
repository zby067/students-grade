# students-grade
基于Flask和阿里云的学生成绩查询系统，支持学生成绩查询、教师成绩管理等功能。

- 学生成绩查询（带时间控制）
- 教师成绩批量导入
- 多角色权限管理
- Excel/csv文件上传处理
- 基于阿里云的云原生架构

- 后端：Python Flask
- 前端：HTML + CSS + JavaScript
- 数据库：SQLite
- 部署平台：阿里云ECS

1. 安装依赖：`pip install -r requirements.txt`
2. 初始化数据库：`python init_db.py`
3. 启动应用：`python app.py`

student-grade-system/

├── app.py # 主应用文件

├── init_db.py # 数据库初始化

├── requirements.txt # 依赖列表

├── templates/ # 模板文件

│ ├── login.html

│ ├── student.html

│ └── teacher.html

└── README.md
