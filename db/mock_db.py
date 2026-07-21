import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT/'db'/'employees.db'

def get_conn(db_path:Path = DB_PATH)->sqlite3.Connection:
    if not db_path:
     raise FileNotFoundError(
        f"[error]数据文件未找到{db_path}"

     )
    conn = sqlite3.connect(str(db_path))
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db(db_path:Path=DB_PATH)->sqlite3.Connection:
    db_path.parent.mkdir(parents=True,exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.execute('PRAGMA foreign_keys = ON')
    cursor = conn.cursor()
    # 创建员工表
    cursor.execute(
        """
        create table if not exists employees(
            uid text primary key,        --员工id
            name text not null,          --姓名
            rank text not null,          --职级
            location text not null,      --工作地点
            seniority integer not null,  --工作年限
            base_salary integer not null --薪资
        )
        """
    )
    # 创建假期表
    cursor.execute("""
      create table if not exists leave_balances(
            uid text primary key,
            annual_leave_remaining integer not null,  --年休假
            sick_leave_remaining integer not null,    --病假
            foreign key(uid) references employees(uid)
        )
    
    """)
    cursor.execute("""delete from employees""")
    cursor.execute("""delete from leave_balances""")
    text_employees = [
        ("1001","张三","P5","南京",5,18000),
        ("1002", "张三", "P4", "北京", 4, 15000),
        ("1003", "张三", "P3", "上海", 3, 12000),
        ("1004", "张三", "P2", "杭州", 2, 10000),
    ]
    test_balances =[
        ("1001",6,10),
        ("1002", 5, 11),
        ("1003", 4, 9),
        ("1004", 3, 10),
    ]
    for emp in text_employees:
        cursor.execute("insert into employees values(?,?,?,?,?,?)", emp)
    for bal in test_balances:
        cursor.execute("insert into leave_balances values(?,?,?)",bal)
    conn.commit()


    print("[success]数据库已创建成功")
    print(f"数据库路径{db_path}")
    return conn

def query(conn:sqlite3.Connection,sql:str,params:tuple=()):
    cursor = conn.cursor()
    cursor.execute(sql,params)
    colums = [col[0] for col in cursor.description] # 获取列名
    return [dict(zip(colums,row))for row in cursor.fetchall()] # fetchall 获取所有行

def close(conn:sqlite3.Connection):
    if conn:
        conn.close()
        print("数据库已经关闭")

if __name__ == "__main__":
    conn = get_conn()
    conn1 = init_db()
    conn2 = get_conn()
    close(conn)
    close(conn1)
    close(conn2)