from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated

"""
用户传入一串员工信息sql（包括姓名、年龄、性别、部门、职务）、员工提交的申请事务内容
提交的状态中，只有员工id，具体的信息由数据库查询
输出审批结果与参考依据
"""


# 定义员工信息状态
class ApplicationState(TypedDict):
    id: str
    application: str  # 员工申请信息
    result: str  # 审核处理结果
    reason: str # 审核原因

# 查询数据库，获取员工信息
def search_node():
    pass


# 将用户的申请，通过rag工具搜索返回结果
def check_node():
    pass