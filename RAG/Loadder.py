from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
import os
from config import embedding
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT/'chroma'/'chroma.db'
doc_path=os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "\\data\\员工手册.txt"

def init_store()->Chroma:
    if DB_PATH.exists():
        return Chroma(persist_directory=str(DB_PATH),embedding_function=embedding)

    loader = TextLoader(
        file_path=doc_path,
        encoding="utf-8"
    )

    docs = loader.load()
    # MarkdownSpliter = MarkdownHeaderTextSplitter(
    # headers_to_split_on=[
    #     ('##','Chapter'),
    #     ('###','Section')
    # ],
    #
    # )

    spliter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=25,
        separators=["\n\n", "\n", "。", "！", "，", " "],
        length_function=len,
    )

    split_docs = spliter.split_documents(docs)


    vector = Chroma.from_documents(
        embedding=embedding,
        persist_directory=str(DB_PATH),
        documents=split_docs,
    )
    return vector

vector_store = init_store()
retriever = vector_store.as_retriever(
    search_kwargs={"k":5}
)


