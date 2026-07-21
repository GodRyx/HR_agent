from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
import os
from config import embedding
from langchain_text_splitters import RecursiveCharacterTextSplitter

loader = TextLoader(
    file_path=os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "\\data\\员工手册.txt",
    encoding="utf-8"
)

docs = loader.load()

spliter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=25,
    separators=["\n\n", "\n", "。", "！", "，", " "],
    length_function=len,
)

split_docs = spliter.split_documents(docs)

Chroma.from_documents(
    embedding=embedding,
    persist_directory=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+"\\db\\chroma",
    documents=split_docs,
)