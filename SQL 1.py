# pip install pyodbc gradio
import pyodbc
import gradio as gr
from datetime import datetime

# ========== 数据库配置 ==========
SERVER = 'localhost'  # 本地服务器
DATABASE = 'ReportServerTempDB'  # 数据库名称
USE_WINDOWS_AUTH = True  # 使用Windows认证


def get_connection():
    """创建并返回数据库连接"""
    if USE_WINDOWS_AUTH:
        connection_string = (
            f'DRIVER={{ODBC Driver 18 for SQL Server}};'
            f'SERVER={SERVER};DATABASE={DATABASE};'
            f'Trusted_Connection=yes;'
            f'Encrypt=no;'
            f'TrustServerCertificate=yes;'
        )
    else:
        connection_string = (
            f'DRIVER={{ODBC Driver 18 for SQL Server}};'
            f'SERVER={SERVER};DATABASE={DATABASE};'
            f'UID={USERNAME};PWD={PASSWORD}'
            f'Encrypt=no;'
            f'TrustServerCertificate=yes;'
        )

    try:
        # 添加字符集设置
        conn = pyodbc.connect(connection_string, autocommit=True)

        # 设置字符编码为UTF-8
        conn.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
        conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
        conn.setdecoding(pyodbc.SQL_WMETADATA, encoding='utf-8')
        conn.setencoding(encoding='utf-8')

        return conn
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")
        return None


# ========== 核心功能函数 ==========
def display_table(table_name):
    """显示指定表的所有数据"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 获取表结构信息
        cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")
        columns = [row.COLUMN_NAME for row in cursor.fetchall()]

        # 查询表数据并转换为字典列表
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = []
        for row in cursor.fetchall():
            row_dict = {}
            for i, col in enumerate(columns):
                # 处理中文字符编码
                if isinstance(row[i], str):
                    row_dict[col] = row[i].encode('latin1').decode('gbk')
                else:
                    row_dict[col] = row[i]
            rows.append(row_dict)

    # 将字典列表转换为适合Dataframe的格式
    data = []
    if rows:
        # 添加表头
        data.append(list(rows[0].keys()))

        # 添加数据行
        for row in rows:
            data.append([row[col] for col in rows[0].keys()])

    return data


def add_student(sno, sname, ssex, sbirth, sclass, sscholarship):
    """添加新学生"""
    # 验证出生年月格式 (YYYY-MM)
    if not validate_birth_format(sbirth):
        return "出生年月格式错误！请使用YYYY-MM格式"

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Student (Sno, Sname, Ssex, Sbirth, Sclass, Sscholarship) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (sno, sname, ssex, sbirth, sclass, sscholarship)
            )
            conn.commit()
        return "学生添加成功！"
    except pyodbc.IntegrityError:
        return "学号已存在！"
    except Exception as e:
        return f"添加失败: {str(e)}"


def add_teacher(tno, tname, tedu, ttitle, tremarks):
    """添加新教师"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Teacher (Tno, Tname, Tedu, Ttitle, Tremarks) "
                "VALUES (?, ?, ?, ?, ?)",
                (tno, tname, tedu, ttitle, tremarks)
            )
            conn.commit()
        return "教师添加成功！"
    except pyodbc.IntegrityError:
        return "教师号已存在！"
    except Exception as e:
        return f"添加失败: {str(e)}"


def add_grade(sno, cno, grade):
    """添加成绩"""
    try:
        grade = int(grade)  # 确保成绩是整数
        if grade < 0 or grade > 100:
            return "成绩必须在0-100之间！"
    except ValueError:
        return "成绩必须是整数！"

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Grade (Sno, Cno, Grade) VALUES (?, ?, ?)",
                (sno, cno, grade)
            )
            conn.commit()
        return "成绩添加成功！"
    except pyodbc.IntegrityError as e:
        if "PRIMARY KEY" in str(e):
            return "该学生的这门课成绩已存在！"
        elif "FOREIGN KEY" in str(e):
            return "学生或课程不存在！"
    except Exception as e:
        return f"添加失败: {str(e)}"


def search_student(name):
    """查询学生详细信息及成绩"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # 查询学生基本信息
        cursor.execute(
            "SELECT Sno, Sname, Ssex, Sbirth, Sclass, Sscholarship "
            "FROM Student WHERE Sname = ?",
            (name,)
        )
        student_info = cursor.fetchone()

        if not student_info:
            return None, []

        # 处理中文字符
        processed_info = []
        for value in student_info:
            if isinstance(value, str):
                processed_info.append(value.encode('latin1').decode('gbk'))
            else:
                processed_info.append(value)

        # 查询学生成绩
        cursor.execute(
            "SELECT c.Cname, g.Grade "
            "FROM Grade g "
            "JOIN Course c ON g.Cno = c.Cno "
            "WHERE g.Sno = ?",
            (student_info.Sno,)
        )
        grades = []
        for row in cursor.fetchall():
            # 处理中文字符
            course_name = row.Cname.encode('latin1').decode('gbk') if isinstance(row.Cname, str) else row.Cname
            grades.append((course_name, row.Grade))

    return processed_info, grades


def validate_birth_format(date_str):
    """验证出生年月格式 (YYYY-MM)"""
    try:
        if len(date_str) != 7 or date_str[4] != '-':
            return False
        year = int(date_str[:4])
        month = int(date_str[5:7])
        current_year = datetime.now().year
        return 1900 < year <= current_year and 1 <= month <= 12
    except ValueError:
        return False


# ========== Gradio 界面 ==========
def create_interface():
    with gr.Blocks(title="学生信息管理系统", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🎓 学生信息管理系统")
        gr.Markdown(f"**数据库连接**: {SERVER} - {DATABASE} (Windows认证)")

        # ===== 数据展示标签 =====
        with gr.Tab("数据展示"):
            table_selector = gr.Dropdown(
                choices=["Student", "Teacher", "Course", "Grade"],
                label="选择数据表",
                value="Student"
            )
            display_btn = gr.Button("显示数据", variant="primary")
            table_output = gr.Dataframe(interactive=False)

        # ===== 添加数据标签 =====
        with gr.Tab("添加数据"):
            with gr.Tab("添加学生"):
                gr.Markdown("### 添加新学生")
                student_inputs = [
                    gr.Textbox(label="学号", max_lines=1, ),
                    gr.Textbox(label="姓名", ),
                    gr.Radio(["男", "女"], label="性别", value="男"),
                    gr.Textbox(label="出生年月 (YYYY-MM)", placeholder="例如: 2000-05", ),
                    gr.Textbox(label="班级"),
                    gr.Textbox(label="奖学金")
                ]
                add_student_btn = gr.Button("添加学生", variant="primary")
                student_output = gr.Textbox()

            with gr.Tab("添加教师"):
                gr.Markdown("### 添加新教师")
                teacher_inputs = [
                    gr.Textbox(label="教师号", max_lines=1, ),
                    gr.Textbox(label="姓名", ),
                    gr.Textbox(label="学历", ),
                    gr.Textbox(label="职称", ),
                    gr.Textbox(label="备注")
                ]
                add_teacher_btn = gr.Button("添加教师", variant="primary")
                teacher_output = gr.Textbox()

            with gr.Tab("添加成绩"):
                gr.Markdown("### 添加学生成绩")
                with gr.Row():
                    sno_input = gr.Textbox(label="学号", )
                    cno_input = gr.Textbox(label="课程号", )
                    grade_input = gr.Number(label="成绩 (0-100)", minimum=0, maximum=100, step=1)
                add_grade_btn = gr.Button("添加成绩", variant="primary")
                grade_output = gr.Textbox()

        # ===== 学生查询标签 =====
        with gr.Tab("学生查询"):
            gr.Markdown("### 查询学生详细信息")
            name_search = gr.Textbox(label="输入学生姓名", placeholder="例如: 张三")
            search_btn = gr.Button("查询学生", variant="primary")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("**学生基本信息**")
                    student_details = gr.Textbox(label="详细信息", interactive=False)

                with gr.Column():
                    gr.Markdown("**学生成绩信息**")
                    grade_table = gr.Dataframe(
                        headers=["课程名称", "成绩"],
                        interactive=False
                    )

        # ===== 事件绑定 =====
        # 数据展示事件
        display_btn.click(
            fn=display_table,
            inputs=table_selector,
            outputs=table_output
        )

        # 添加学生事件
        add_student_btn.click(
            fn=add_student,
            inputs=student_inputs,
            outputs=student_output
        )

        # 添加教师事件
        add_teacher_btn.click(
            fn=add_teacher,
            inputs=teacher_inputs,
            outputs=teacher_output
        )

        # 添加成绩事件
        add_grade_btn.click(
            fn=add_grade,
            inputs=[sno_input, cno_input, grade_input],
            outputs=grade_output
        )

        # 学生查询事件
        def search_handler(name):
            result = search_student(name)
            if result[0]:
                info = result[0]
                details = f"学号: {info[0]}\n姓名: {info[1]}\n性别: {info[2]}\n" \
                          f"出生年月: {info[3]}\n班级: {info[4]}\n奖学金: {info[5]}"
                grades = [[row[0], row[1]] for row in result[1]]
                return details, grades
            else:
                return "找不到该学生", []

        search_btn.click(
            fn=search_handler,
            inputs=name_search,
            outputs=[student_details, grade_table]
        )

    return app


if __name__ == "__main__":
    # 测试数据库连接
    try:
        test_conn = get_connection()
        if test_conn:
            print("✅ 数据库连接成功")
            test_conn.close()
        else:
            print("❌ 数据库连接失败，请检查配置")
    except Exception as e:
        print(f"❌ 数据库连接错误: {str(e)}")

    # 启动应用
    app = create_interface()
    app.launch(server_port=7860, share=False)