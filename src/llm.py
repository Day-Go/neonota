from queue import Queue
from openai import OpenAI
from database_client import DbClient

class LLM:
    def __init__(self, chat_model: str, embed_model: str, db_client: DbClient):
        self.chat_model = chat_model
        self.embed_model = embed_model
        self.db_client = db_client
        self.llm_client = OpenAI()

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        completion = self.llm_client.chat.completions.create(
            model = self.chat_model,
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        return str(completion.choices[0].message.content)

    def embed(self, input: str) -> list[float]:
        print(input)
        response = self.llm_client.embeddings.create(
            model=self.embed_model,
            input=input
        )
        return response.data[0].embedding
