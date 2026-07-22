from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
import os

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from config import embedding, llm
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from pathlib import Path
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from sentence_transformers import SentenceTransformer
from config import embedding,reranker
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT/'chroma'/'chroma.db'
doc_path=os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "\\data\\员工手册.txt"

def build_ensemble_retriever():
    """构建BM25+vector的混合检索"""
    loader = TextLoader(
        file_path=doc_path,
        encoding="utf-8"
    )

    docs = loader.load()
    # with open(doc_path,"r",encoding="utf-8")as f:
    #     markdown = f.read()
    # markdown_spliter = MarkdownHeaderTextSplitter(
    # headers_to_split_on=[
    #     ('##','Chapter'),
    #     ('###','Section')
    # ],
    # )
    # md_header_splits = markdown_spliter.split_text(markdown)
    spliter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=25,
        separators=["\n\n", "\n", "。", "！", "，", " "],
        length_function=len,
    )

    split_docs = spliter.split_documents(docs)

    #路线a：BM25检索
    BM25_retriever=BM25Retriever.from_documents(split_docs)
    BM25_retriever.k=5
    #路线b：
    if DB_PATH.exists():
        vector_retriever = Chroma(persist_directory=str(DB_PATH),embedding_function=embedding).as_retriever(search_kwargs={"k":5})

    else:
        vector_store=Chroma.from_documents(
            documents=split_docs,
            embedding=embedding,
            persist_directory=str(DB_PATH),
            collection_name="worker_book"
        )
        vector_retriever = vector_store.as_retriever(search_kwargs={"k":5})

    ensemble_retriever = EnsembleRetriever(
        retrievers=[vector_retriever,BM25_retriever],
        weights=[0.6,0.4],# 40%依赖于文档，60%依赖于语义泛化
    )

    return ensemble_retriever

retriever = build_ensemble_retriever()

# 智能扩写与HDye

class   QueryExpansion(BaseModel):
    expanded_query:list[str] =Field(description="从三个角度不同扩写问题"),
    hypothetical_documents : str =Field(description="针对该问题的一段假设性、看似专业的回答片段，允许伪造数字")

expansion_parser =JsonOutputParser(pydantic_object=QueryExpansion)

def expan_and_hyde(query:str)->list[str]:
    prompt=ChatPromptTemplate.from_template( """
    你是一个专业的HR,你需要按照配置格式要求，返回对应的json文件：
    1、将问题扩写成三个不同的角度
    2、针对这个问题，基于一般员工管理准则，生成一段假设性文档，用于检验
    用户原始问题：{query}
    配置：{expansion}
    """)
    chain = prompt|llm|expansion_parser
    result = chain.invoke({
        "query":query,
        "expansion":expansion_parser.get_format_instructions()
    })
    print(result)
    return [query]+result["expanded_query"]+[result["hypothetical_documents"]]



