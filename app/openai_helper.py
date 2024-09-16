from openai import OpenAI
from config import Config
import time

client = OpenAI(api_key=Config.OPENAI_API_KEY)

assistant = client.beta.assistants.create(
    name="Journal Prompt Generator",
    instructions="You are a friend that generates prompts based on journal entries.",
    model="gpt-4o"
)

def generate_prompt():
    thread = client.beta.threads.create()
    
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=(
            "Generate a light-hearted journaling prompt that asks about my day in a fun, conversational way. "
            "It should feel like I'm chatting with a friend, making it easy for me to reflect on what happened today."
        )
    )
    
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        time.sleep(0.5)
    
    if run.status == "failed":
        return "What's on your mind today?"
    
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value

