from RAG.Loadder import init_store
from langchain.tools import tool

from config import reranker
from RAG.rag_pipeline2 import expan_and_hyde
retriever = init_store().as_retriever(kwargs={"k":5})

@tool
def search_hr(query:str):
    """用于查询员工手册信息"""
    docs = retriever.invoke(query)
    if not docs:
        return "查找信息不存在"
    result = ""
    for doc in docs:
        result += doc.page_content
    return result

@tool

def search_hr_policy(query:str):
    """高级知识搜索引擎
    当用户询问关于公司规章制度、差旅报销标准，假期政策，福利相关时，必须调用此工具，输入参数query是用户原始问题
    """
    search_queries =expan_and_hyde(query)
    # 多路并发检索
    all_condition_docs=[]
    for q in search_queries:
        docs = retriever.invoke(q)
        all_condition_docs.extend(docs)

    # 文档去重，采用将文档内容收集为集合，利用集合不可重复性进行去重
    unique_docs = {doc.page_content: doc for doc in all_condition_docs}.values()
    unique_docs =list(unique_docs)
    if not unique_docs:
        return "没有相关政策，请咨询HR人工"

    sentence_pairs = [[query,doc.page_content] for doc in unique_docs]
    scores = reranker.predict(sentence_pairs)

    scored_doc = list(zip(unique_docs,scores))
    scored_doc.sort(key=lambda x:x[1],reverse=True)

    top_3_docs = [doc for doc,_ in scored_doc[:3]]

    context_pairs=[]
    for i ,doc in enumerate(top_3_docs,1):
        chapter = doc.metadata.get("Chapter","未知章节")
        section = doc.metadata.get("Section","未知段落")
        context_pairs.append(f"来源：{i}{chapter}>{section}\n{doc.page_content}")
    merged_context ="\n\n".join(context_pairs)
    return f"检索结果：\n{merged_context}"