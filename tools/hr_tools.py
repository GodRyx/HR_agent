import atexit  # 常用于执行资源释放、文件关闭、日志记录等收尾工作

from langchain.tools import tool

from db.mock_db import get_conn, query, close

db_conn = get_conn()
atexit.register(close, db_conn)  # 注册进程退出时的清理钩子hook
import sys
from pathlib import Path

PROJECT_ROOT=Path(__file__).resolve().parent.parent # 自动将项目根目录挂载到环境变量中，避免出现Modelnotfound错误
sys.path.append(str(PROJECT_ROOT))

@tool
def get_employee_profile(uid: str) -> str:
    """
    根据员工uid查询员工信息，包括姓名，职级，年限，基本薪资，工作城市
    当需要获取员工信息时，必须调用此工具
    :param uid: 
    :return: 
    """
    sql = "select uid,name,rank,location,seniority,base_salary from employees where uid = ?"
    res = query(conn=db_conn, sql=sql, params=(uid,))

    if not res:
        return f"[error]未找到uid为{uid}的员工"
    else:
        employee = res[0]
        return (f"""
        查询结果：
        姓名：{employee['name']}
        职级：{employee['rank']}
        工作年限：{employee['seniority']}
        工作地点：{employee['location']}
        基本薪资：{employee['base_salary']}元
        
        """)





@tool
def get_employee_balance(uid: str):
    """用于查询员工剩余假期"""

    sql = "select name, annual_leave_remaining,sick_leave_remaining  from leave_balances left join employees on employees.uid = leave_balances.uid  where employees.uid = ?"
    res = query(conn=db_conn, sql=sql, params=(uid,))

    if not res:
        return f"[error]未找到uid为{uid}的员工"
    else:
        balances = res[0]
        return f"查询结果：\n员工：{balances["name"]}\n剩余年假：{balances['annual_leave_remaining']}\n剩余病假：{balances['sick_leave_remaining']}"



@tool
def generate_employment_certificate(uid:str,cer_type:str)->str:
    """为指定员工自动生成证明文件
    employment 仅在开具在职证明，全员可用
    income 开具包含薪资的在职及收入证明
    """
    sql = "select name,rank,base_salary from employees where uid = ?"
    emp_res = query(conn=db_conn,sql=sql,params=(uid,))

    if not emp_res:
        return f"不存在该工号员工：{uid}"
    employee =emp_res[0]
    if cer_type =="income":
        try:
            rank_level = int(employee["rank"].replace("P",""))
        except:
            rank_level=0
        if rank_level<5:
            return f"当前员工职级为{employee['rank']},小于5级，不支持在线生成工资证明\n请联系hr线下开办证明"

        content = f"当前员工姓名{employee['name']},\n员工职级{employee['rank']},\n员工基本薪资{employee['base_salary']}"
        return f"已生成工资证明\n{content}\n（公章）"

    if cer_type =="employment":
        content = f"当前员工姓名{employee['name']},\n员工职级{employee['rank']}"
        return f"已生成在职证明\n{content}\n（公章）"

    return "指令错误，不为employment或income"
