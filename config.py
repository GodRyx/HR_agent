from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer
from sentence_transformers import CrossEncoder
import os
load_dotenv()

# 基础大模型
llm = init_chat_model(os.getenv("deepseek_model"))

# 向量压缩模型
from langchain_huggingface import HuggingFaceEmbeddings

embedding = HuggingFaceEmbeddings(
    model_name=os.getenv("EMB_DIR"),  # 本地路径也可以
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

#重排模型
reranker = CrossEncoder(os.getenv("CROSS_DIR"),max_length=512)

# 改写模型
change_llm = ChatOpenAI(
    api_key=os.getenv("deepseek_api_key"),
    base_url=os.getenv("deepseek_base_url"),
    model=os.getenv("deepseek_model"),
    temperature=0.7
)

local_llm = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    model="E:\\大模型\\模型\\lmstudio-community\\Qwen3-4B-GGUF\\Qwen3-4B-Q4_K_M.gguf",
    api_key="gvjgv"
)

# r = local_llm.invoke("你好")
# print(r)