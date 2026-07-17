from langchain_nvidia_ai_endpoints import ChatNVIDIA
from dotenv import load_dotenv
import os
load_dotenv()

llm = ChatNVIDIA(
    api_key=os.getenv("NVIDIA_API_KEY"),
    model="meta/llama-4-scout-17b-16e-instruct",
    temperature=0.2,
    top_p=0.7,
)
