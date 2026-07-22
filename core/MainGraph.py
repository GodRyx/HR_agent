from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import add_messages,StateGraph,START,END
from typing import TypedDict, Annotated
from langchain_core.messages import SystemMessage, BaseMessage, HumanMessage
from langgraph.prebuilt import ToolNode, tools_condition
from tools.RagTool import search_hr_policy
from config import llm, local_llm
from pydantic import BaseModel, Field

"""
用户传入一串员工信息sql（包括姓名、年龄、性别、部门、职务）、员工提交的申请事务内容
提交的状态中，只有员工id，具体的信息由数据库查询
输出审批结果与参考依据
"""

# 给模型绑定工具参数
tools = [search_hr_policy]
llm_bind_tools = llm.bind_tools(tools=tools)


# 定义员工信息状态
class ApplicationState(TypedDict):
    id: str  # 员工id
    application: str  # 员工申请信息
    messages: Annotated[list[BaseMessage], add_messages]  # 消息列表
    result: str  # 审核处理结果
    reason: str  # 审核原因
    loop_num: int  # 模型循环次数


# 查询数据库，获取员工信息
def search_node():
    pass


class Application(BaseMessage):
    result: str = Field(description="审核结果建议")
    reason: str = Field(description="审核原因")


class Check(BaseMessage):
    feedback: str = Field(description="检验返回")
    reason: str = Field(description="审核原因")


# 将用户的申请，通过rag工具搜索返回结果
def chat_node(state: ApplicationState):
    messages = state.get("messages", [])
    if len(messages) == 0:
        application = state.get("application", "")  # 获取员工信息请求

        print(f"收到用户请求{application}")

        if not application:
            print("用户请求为空")
            return {"result": "处理失败", "reason": "请求为空"}

        messages += [SystemMessage(
            content="你是一个专业的HR，你需要根据用户申请，调用知识库搜索工具，查找员工手册信息，给予反馈建议和原因")]
        messages += [HumanMessage(content=application)]
    print(f"正在进行第{state.get("loop_num", 0) + 1}轮查询检验")
    response = llm_bind_tools.invoke(messages)
    return {"messages": [response], "loop_num": state.get("loop_num", 0) + 1}


tool_node = ToolNode(tools=tools)


# 审计节点，回调找到rag的返回结果，与问题进行事实检验
def check_node(state: ApplicationState):
    print("正在审计")
    messages = state.get("messages", [])
    message = messages[-1].content
    print(f"模型输出内容：{message}")
    rag_content = ""
    for msg in reversed(messages):
        if getattr(msg, "name", "") == "search_hr_policy":
            rag_content = msg.content
            print(f"检索内容：{rag_content}")
            break

    if not rag_content:
        print("没有找到检索结果")
        return {}

    check_parser = JsonOutputParser(pydantic_object=Check)

    prompt = ChatPromptTemplate.from_template("""
    你是一个严格的回答检验者，你需要根据查询知识和回复，判定生成是否产生了幻觉，你需要返回json格式的内容，包括是否通过（pass/fail），以及修改建议
    rag检索内容：{rag}
    模型回答：｛re｝
    输出结构：{check_parser}
    """)
    chain = prompt | local_llm | check_parser
    print("开始审核")
    result_ = chain.invoke({"rag": rag_content, "re": message, "check_parser": check_parser.get_format_instructions()})
    if result_["feedback"] == "fail":
        print("发现幻觉")
        return {"messages": [HumanMessage(content=f"你的输出出现了幻觉，原因：{result_['reason']},请重新输出")]}
    else:
        print("输出合法")
        return {}

def final_node(state:ApplicationState):
    print("正在进行总结")
    messages = state.get("messages", [])
    if not len(messages) == 0:
        final_parser = JsonOutputParser(pydantic_object=Application)
        prompt = ChatPromptTemplate.from_template("""
            你是一个消息总结助手，你需要提取结果，返回json格式的内容
            大模型输出：{re}
            输出结构：{final_parser}
            """)
        chain = prompt | local_llm | final_parser
        result_ = chain.invoke({"re":state['messages'][-1].content, "final_parser": final_parser.get_format_instructions()})
    return {"result":result_["result"], "reason":result_["reason"]}

def router(state:ApplicationState):
    messages = state.get("messages", [])
    if not len(messages) == 0:
        if isinstance(state["messages"][-1],HumanMessage) and state["loop_num"]<4:
            return "chat"

    return "final"

graph = (
    StateGraph(ApplicationState)
    .add_node("chat",chat_node)
    .add_node("check",check_node)
    .add_node("tools",tool_node)
    .add_node("final",final_node)
    .add_edge(START,"chat")
    .add_conditional_edges("chat",tools_condition,{"tools":"tools","__end__":"check"})
    .add_edge("tools","chat")
    .add_conditional_edges("check",router)
    .add_edge("final",END)
    .compile()
)

result = graph.stream({"application":"我想申请14号发工资"},stream_mode="updates")
for r in result:
    print(r)
# print(f"处理结果：{result['result']},处理原因：{result['reason']}")