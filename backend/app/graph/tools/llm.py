from langchain_nvidia_ai_endpoints import ChatNVIDIA
from dotenv import load_dotenv
import os

load_dotenv()

# Model name is read from env so it can be swapped without a code change.
# See context/issues/01-issue.md for the deprecation warning and model options.
_model = os.getenv("NVIDIA_MODEL", "meta/llama-4-maverick-17b-128e-instruct")

llm = ChatNVIDIA(
    api_key=os.getenv("NVIDIA_API_KEY"),
    model=_model,
    temperature=0.2,
    top_p=0.7,
)
