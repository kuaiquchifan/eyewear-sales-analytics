import os
import re
from pathlib import Path
import json

import torch
import gradio as gr
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from sentence_transformers import SentenceTransformer


# -----------------------------
# 1. 路径配置
# -----------------------------


BASE = Path(__file__).resolve().parent.parent
print(f"BASE path: {BASE}")
META_PATH = BASE / "7-2-build_index" / "build_index" / "knowledge_meta.json"
print(f"META_PATH: {META_PATH}")
API_KEY_FILE = BASE/ "7-3-retrieval" / "api-key.txt"
print(f"API_KEY_FILE: {API_KEY_FILE}")

MODEL_PATH = r"D:\huggingface_models\BAAI_bge_base_en_v15"
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")


# -----------------------------
# 2. 本地 SentenceTransformer 包装成 LangChain Embeddings
# -----------------------------
class LocalSentenceEmbeddings(Embeddings):
    def __init__(self, model_path: str, device: str = "cpu"):
        self.model = SentenceTransformer(
            model_path,
            device=device,
            local_files_only=True
        )

    def embed_documents(self, texts):
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=32
        ).astype("float32")
        return embeddings.tolist()

    def embed_query(self, text):
        embedding = self.model.encode(
            [text],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False
        ).astype("float32")
        return embedding[0].tolist()


# -----------------------------
# 3. 读取知识库元数据
# -----------------------------
with open(META_PATH, "r", encoding="utf-8") as f:
    docs = json.load(f)

# 过滤只保留 customer cluster 相关知识，保持与你原来逻辑一致
filtered_docs = []
for d in docs:
    source = str(d.get("source_file", "")).lower()
    if "customer_cluster" in source:
        filtered_docs.append(d)

if not filtered_docs:
    raise ValueError("未找到 customer cluster 相关知识，请检查 knowledge_meta.json 是否正确。")

documents = [
    Document(
        page_content=d.get("text", ""),
        metadata={
            "id": d.get("id"),
            "source_file": d.get("source_file"),
        }
    )
    for d in filtered_docs
]


# -----------------------------
# 4. 读取 DeepSeek Key
# -----------------------------
def load_deepseek_key(file_path: Path) -> str:
    text = file_path.read_text(encoding="utf-8")
    match = re.search(r"sk-[A-Za-z0-9]+", text)
    if not match:
        raise ValueError(f"未在 {file_path} 中找到 DeepSeek API Key")
    return match.group(0)


DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") or load_deepseek_key(API_KEY_FILE)


# -----------------------------
# 5. 构建 LangChain 向量库
# -----------------------------
embedding = LocalSentenceEmbeddings(MODEL_PATH, device=device)
vectorstore = FAISS.from_documents(documents, embedding)

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 10}
)


# -----------------------------
# 6. 构造 Prompt
# -----------------------------
prompt_template = """
你是一个眼镜零售数据分析助手。

请严格根据以下 customer cluster 知识回答问题，不能编造，不能混入门店、活动、FAQ 或其他业务知识。

你需要按以下格式输出：
- Cluster 0: ...
- Cluster 1: ...
- Cluster 2: ...
- Cluster 3: ...

上下文：
{context}

问题：
{question}

输出要求：
1. 先给总体结论
2. 再按 cluster 顺序逐个说明
3. 只使用上下文中的事实
"""

PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"]
)


# -----------------------------
# 7. 初始化 LLM
# -----------------------------
llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
    temperature=0.2
)


# -----------------------------
# 8. 构建 QA Chain
# -----------------------------
prompt = PromptTemplate.from_template("""
你是一个眼镜零售数据分析助手。

请严格根据以下 customer cluster 知识回答问题，不能编造，不能混入门店、活动、FAQ 或其他业务知识。

上下文：
{context}

问题：
{question}
""")

qa_chain = (
    {
        "context": retriever,
        "question": RunnablePassthrough()
    }
    | prompt
    | llm
    | StrOutputParser()
)


# -----------------------------
# 9. 业务函数：调用 RAG
# -----------------------------
def ask(question: str):
    if not question or not question.strip():
        return "请输入问题。", ""
    try:
        answer = qa_chain.invoke(question)
        source_docs = retriever.invoke(question)
        retrieval_text = "\n\n".join(
            f"Rank {i+1}: {doc.metadata.get('source_file', '')}\n{doc.page_content[:500]}"
            for i, doc in enumerate(source_docs)
        )
        return answer, retrieval_text
    except Exception as e:
        return f"调用失败：{str(e)}", ""


# -----------------------------
# 10. Gradio 界面
# -----------------------------
demo = gr.Interface(
    fn=ask,
    inputs=gr.Textbox(lines=2, placeholder="比如：每个 customer cluster 的特征是什么？"),
    outputs=[
        gr.Textbox(label="DeepSeek 回答"),
        gr.Textbox(label="检索结果")
    ],
    title="Customer Cluster RAG (LangChain)"
)

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=True)