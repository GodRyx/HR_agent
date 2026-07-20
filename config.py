from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from sentence_transformers import SentenceTransformer
from sentence_transformers import CrossEncoder
import os
load_dotenv()
# 基础大模型
llm = init_chat_model(os.getenv("deepseek_model"))

# 向量压缩模型
embedding = SentenceTransformer(os.getenv("EMB_DIR"))

#重排模型
reranker = CrossEncoder(os.getenv("CROSS_DIR"))