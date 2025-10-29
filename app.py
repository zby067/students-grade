from flask import Flask, request, jsonify, render_template, session, redirect
import sqlite3
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__, template_folder='templates')
app.secret_key = 'student-system-key-2024'
app.config['UPLOAD_FOLDER'] = 'uploads'

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect('student.db')
    conn.row_factory = sqlite3.Row
    return conn

# 首页和登录
@app.route('/')
def index():
    """首页 - 跳转到登录页面"""
    if 'user_id' in session:
        if session['role'] == 'student':
            return redirect('/student')
        else:
            return redirect('/teacher')
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """处理用户登录"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    conn = get_db()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ? AND password = ?', 
        (username, password)
    ).fetchone()
    
    if user:
        # 登录成功，设置session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['name'] = user['name']
        conn.close()
        
        # 根据角色重定向到不同页面
        if user['role'] == 'student':
            return redirect('/student')
        else:
            return redirect('/teacher')
    else:
        conn.close()
        return render_template('login.html', error='用户名或密码错误')

@app.route('/logout')
def logout():
    """用户注销"""
    session.clear()
    return redirect('/')

# 学生功能
@app.route('/student')
def student_page():
    """学生主页"""
    if 'user_id' not in session or session['role'] != 'student':
        return redirect('/')
    
    conn = get_db()
    
    # 获取学生信息
    student = conn.execute(
        'SELECT * FROM users WHERE id = ?', (session['user_id'],)
    ).fetchone()
    
    # 检查查询时间段
    period = conn.execute(
        'SELECT * FROM query_periods WHERE is_active = 1'
    ).fetchone()
    
    can_query = True
    period_info = None
    if period:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if now < period['start_date'] or now > period['end_date']:
            can_query = False
        period_info = f"{period['start_date']} 至 {period['end_date']}"
    
    # 获取学生成绩
    grades = []
    if can_query:
        grades = conn.execute('''
            SELECT course_name, score, semester, academic_year 
            FROM grades WHERE student_id = ?
            ORDER BY academic_year DESC, semester DESC
        ''', (student['student_id'],)).fetchall()
    
    conn.close()
    
    return render_template('student.html',
                         student=dict(student),
                         grades=[dict(grade) for grade in grades],
                         can_query=can_query,
                         period_info=period_info)

# 教师功能
@app.route('/teacher')
def teacher_page():
    """教师主页"""
    if 'user_id' not in session or session['role'] not in ['teacher', 'admin']:
        return redirect('/')
    
    conn = get_db()
    
    # 获取所有学生列表
    students = conn.execute(
        'SELECT student_id, name, class FROM users WHERE role = "student" ORDER BY class, student_id'
    ).fetchall()
    
    # 获取所有成绩
    grades = conn.execute('''
        SELECT g.student_id, g.course_name, g.score, g.semester, g.academic_year,
               u.name as student_name, u.class
        FROM grades g 
        JOIN users u ON g.student_id = u.student_id 
        ORDER BY g.academic_year DESC, g.semester DESC
    ''').fetchall()
    
    # 获取当前查询时间段
    period = conn.execute(
        'SELECT * FROM query_periods WHERE is_active = 1'
    ).fetchone()
    
    conn.close()
    
    return render_template('teacher.html',
                         students=[dict(student) for student in students],
                         grades=[dict(grade) for grade in grades],
                         period=dict(period) if period else None,
                         user={'name': session['name']})

# API接口 - 教师插入单个成绩
@app.route('/api/insert_grade', methods=['POST'])
def insert_grade():
    """教师插入单个学生成绩"""
    if 'user_id' not in session or session['role'] not in ['teacher', 'admin']:
        return jsonify({'success': False, 'error': '未授权访问'})
    
    data = request.get_json()
    student_id = data.get('student_id')
    course_name = data.get('course_name')
    score = data.get('score')
    semester = data.get('semester')
    academic_year = data.get('academic_year')
    
    # 验证输入数据
    if not all([student_id, course_name, score, semester, academic_year]):
        return jsonify({'success': False, 'error': '请填写所有字段'})
    
    conn = get_db()
    
    try:
        # 检查学生是否存在
        student = conn.execute(
            'SELECT id FROM users WHERE student_id = ? AND role = "student"', 
            (student_id,)
        ).fetchone()
        
        if not student:
            conn.close()
            return jsonify({'success': False, 'error': '学生不存在'})
        
        # 插入成绩
        conn.execute('''
            INSERT INTO grades (student_id, course_name, score, semester, academic_year)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_id, course_name, float(score), semester, academic_year))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '成绩插入成功'})
        
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': f'插入失败: {str(e)}'})

# API接口 - 批量导入成绩
@app.route('/api/upload_grades', methods=['POST'])
def upload_grades():
    """教师批量导入成绩"""
    if 'user_id' not in session or session['role'] not in ['teacher', 'admin']:
        return jsonify({'success': False, 'error': '未授权访问'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    # 检查文件类型
    allowed_extensions = {'.xlsx', '.xls', '.csv'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return jsonify({'success': False, 'error': '只支持Excel和CSV文件'})
    
    try:
        # 保存文件
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 读取文件
        if file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        
        # 验证文件格式
        required_columns = ['学号', '课程名称', '成绩', '学期', '学年']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'success': False, 'error': f'文件必须包含以下列: {required_columns}'})
        
        conn = get_db()
        success_count = 0
        errors = []
        
        # 处理每一行数据
        for index, row in df.iterrows():
            try:
                student_id = str(row['学号']).strip()
                course_name = str(row['课程名称']).strip()
                score = float(row['成绩'])
                semester = str(row['学期']).strip()
                academic_year = str(row['学年']).strip()
                
                # 验证成绩范围
                if score < 0 or score > 100:
                    errors.append(f"第{index+2}行: 成绩 {score} 不在有效范围内 (0-100)")
                    continue
                
                # 检查学生是否存在
                student = conn.execute(
                    'SELECT id FROM users WHERE student_id = ? AND role = "student"', 
                    (student_id,)
                ).fetchone()
                
                if not student:
                    errors.append(f"第{index+2}行: 学号 {student_id} 不存在")
                    continue
                
                # 插入或更新成绩
                conn.execute('''
                    INSERT OR REPLACE INTO grades (student_id, course_name, score, semester, academic_year)
                    VALUES (?, ?, ?, ?, ?)
                ''', (student_id, course_name, score, semester, academic_year))
                
                success_count += 1
                
            except ValueError:
                errors.append(f"第{index+2}行: 成绩格式错误")
            except Exception as e:
                errors.append(f"第{index+2}行: 数据处理错误 - {str(e)}")
        
        conn.commit()
        conn.close()
        
        # 返回处理结果
        result = {
            'success': True,
            'message': f'成功导入 {success_count} 条成绩记录',
            'imported_count': success_count,
            'error_count': len(errors)
        }
        
        if errors:
            result['errors'] = errors[:10]  # 只返回前10个错误
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'文件处理失败: {str(e)}'})

# API接口 - 设置查询时间段
@app.route('/api/set_period', methods=['POST'])
def set_period():
    """设置成绩查询时间段"""
    if 'user_id' not in session or session['role'] not in ['teacher', 'admin']:
        return jsonify({'success': False, 'error': '未授权访问'})
    
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    # 验证时间格式
    if not start_date or not end_date:
        return jsonify({'success': False, 'error': '请填写开始时间和结束时间'})
    
    if start_date >= end_date:
        return jsonify({'success': False, 'error': '开始时间必须早于结束时间'})
    
    conn = get_db()
    
    try:
        # 禁用所有现有时间段
        conn.execute('UPDATE query_periods SET is_active = 0')
        
        # 创建新时间段
        conn.execute('''
            INSERT INTO query_periods (start_date, end_date, is_active)
            VALUES (?, ?, 1)
        ''', (start_date, end_date))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '查询时间段设置成功'})
        
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': f'设置失败: {str(e)}'})

if __name__ == '__main__':
    print("=" * 50)
    print("学生成绩查询系统启动成功！")
    print("访问地址: http://172.19.10.93:5000")
    print("测试账号:")
    print("  - 管理员: admin / admin123")
    print("  - 教师: teacher / teacher123")  
    print("  - 学生: stu2024001 / 2024001")
    print("  - 学生: stu2024002 / 2024002")
    print("=" * 50)
    
    # 检查数据库是否存在
    if not os.path.exists('student.db'):
        print("正在初始化数据库...")
        os.system('python3 init_db.py')
    
    app.run(host='0.0.0.0', port=5000, debug=True)