import ast
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI

from src.prompts import prompt_final_answer, prompt_query_rewrite, prompt_context_relevance
from src.utils import extract_json_str
from src.config import STOP_TOKENS, LLM_API_KEY, LLM_BASE_URL, BASE_MODEL, NUM_CTX, NUM_PREDICT

class LLMProcessor:
    def __init__(
        self,
        base_url: str = LLM_BASE_URL,
        api_key: str = LLM_API_KEY,
        model: str = BASE_MODEL,
        num_ctx: int = NUM_CTX,
        num_predict: int = NUM_PREDICT
    ):
        self.llm = OpenAI(
            base_url=base_url,
            model=model,
            api_key=api_key,
            max_tokens=-1,
            streaming=True,
            verbose=False,
        )

    def build_context(self, sources: list[dict]) -> str:
        context = ""
        for source in sources:
            name = source.get("name", "Unknown")
            page = source.get("page", "Unknown")
            content = source.get("content")
            context += f"Source: {name}, Page: {page}\n```{content}```\n\n"
        return context

    async def query_rewrite(
        self,
        message: str,
        chat_history: list[dict[str, str]],
        prompt_template: PromptTemplate = prompt_query_rewrite
    ):
        prompt = prompt_template.format(chat_history=chat_history, message=message)  
        rewritten_query, fallback_message = None, "Sorry, I can not provide a response at the moment."
        try:
            raw_response = await self.llm.ainvoke(prompt)
            parsed_response = ast.literal_eval(extract_json_str(raw_response))
            valid = parsed_response.get("valid", "false").lower() == "true"
            if valid:
                rewritten_query = parsed_response.get("output")
            else:
                fallback_message = parsed_response.get("output")
        except:
            pass   
        return rewritten_query, fallback_message
        
    async def check_context_relevance(
        self,
        message: str,
        context: str,
        prompt_template: PromptTemplate = prompt_context_relevance
    ):
        prompt = prompt_template.format(context=context, message=message)
        res = await self.llm.ainvoke(prompt)
        try:
            json_str = extract_json_str(res)
            output = ast.literal_eval(json_str)
            rating_raw = output.get("rating")
            rating = int(rating) if str(rating_raw).isdigit() else 1
            return rating >= 2
        except:
            return False

    async def final_answer(
        self,
        message: str,
        context: str,
        prompt_template: PromptTemplate = prompt_final_answer
    ):
        prompt = prompt_template.format(context=context, message=message)
        stop = False
        async for chunk in self.llm.astream(prompt):
            for token in STOP_TOKENS:
                if token in chunk:
                    stop = True
                    break
            if stop:
                break
            yield chunk

