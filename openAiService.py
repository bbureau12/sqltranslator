import os
import time
from openai import OpenAI

from settingsRepository import SettingRepository
from sqlRepository import SqlRepository
#Points of expansion:
#B. Substitute commonly used clauses with A and B (example: SELECT * FROM USERS becomes A) to reduce syllable count from Open AI 
class OpenAiService:

    def __init__(self, settingsRepository: SettingRepository, sqlRepository: SqlRepository):
        self.settingRepository = settingsRepository
        self.sqlRepository = sqlRepository
        #note: open ai ID needs to be in environment variables
        self.client = OpenAI()
        self.assistant_id = os.environ.get("OPENAI_ASSISTANT_ID") or self._create_and_cache_assistant()

        self.assistant = self.client.beta.assistants.create(
            name="SQL Assistant",
            instructions="Translate natural language into SQLite queries based on provided schema. Do not include ID columns. Alias columns in Title Case.",
            tools=[],
            model="gpt-4"
        )
    def _create_and_cache_assistant(self):
        assistant = self.client.beta.assistants.create(
            name="SQL Assistant",
            instructions=(
                "Translate natural language into SQLite queries based on provided schema. "
                "Do not include ID columns. Alias columns in Title Case. "
                "Replace underscores with spaces."
            ),
            tools=[],
            model="gpt-4"
        )
    
        print(f"Created new assistant: {assistant.id} — store this in OPENAI_ASSISTANT_ID")
        assistant_id = assistant.id
        os.environ["OPENAI_ASSISTANT_ID"] = assistant_id

        return assistant.id
    
    def convert_to_sql(self, phrase):
        SQL_PROMPT_TEMPLATE = """
        Given the following table schemas:
        {schemas}

        Translate the natural language query to SQLite.
        - Do not include ID columns.
        - Alias columns with title case (e.g., 'Customer Name').
        - Replace underscores with spaces.

        Query: {query}
        """
        schemas = self.sqlRepository.getSchema()
        prompt = SQL_PROMPT_TEMPLATE.format(schemas=schemas, query=phrase)
        thread = self.client.beta.threads.create()
        self.client.beta.threads.messages.create(
            thread_id = thread.id,
            role = "user",
            content = prompt
        )
        
        run = self.client.beta.threads.run.create(
            thread_id = thread.id,
            assistant_id= self.assistant.id
        )
        while True:
            run = self.client.beta.threads.run.retrieve(
                thread_id=thread.id,
                run_id = run.id
            )
            if run.status == "completed":
                break
            elif run.status in ("failed", "canceled", "expired"):
                raise Exception(f"run failed with status of: {run.status}")
            time.sleep(1)
        messages = self.client.beta.threads.messages.list(thread_id=thread.id)
        for message in reversed(messages.data):
            if message.role == "assistant":
                sql_query = message.content[0].text.value
                if not sql_query.strip().upper().startswith("SELECT"):
                    raise ValueError(f"Unsafe query returned: {sql_query}")
                return sql_query
        return None    