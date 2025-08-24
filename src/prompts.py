import os
from langchain_core.prompts import PromptTemplate

from src.config import TEMPLATE_FINAL_ANSWER, TEMPLATE_QUERY_REWRITE, TEMPLATE_CONTEXT_RELEVANCE

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

template_final_answer_path = os.path.join(PROJECT_ROOT, TEMPLATE_FINAL_ANSWER)
template_query_rewrite_path = os.path.join(PROJECT_ROOT, TEMPLATE_QUERY_REWRITE)
template_context_relevance_path = os.path.join(PROJECT_ROOT, TEMPLATE_CONTEXT_RELEVANCE)

with open(template_final_answer_path, "r") as f:
    template_final_answer = f.read()
with open(template_query_rewrite_path, "r") as f:
    template_query_rewrite = f.read()
with open(template_context_relevance_path, "r") as f:
    template_context_relevance = f.read()

prompt_final_answer = PromptTemplate.from_template(template_final_answer)
prompt_query_rewrite = PromptTemplate.from_template(template_query_rewrite)
prompt_context_relevance = PromptTemplate.from_template(template_context_relevance)