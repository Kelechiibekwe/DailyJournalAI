# from openai import OpenAI
import openai
from config import Config
from app.models import db, Prompts, Responses, User_Prompt
import time
import numpy as np
import redis
import json

# Set embedding model and chat model
embedding_model = "text-embedding-ada-002"
chat_model = "gpt-4o-mini"

# In-memory short-term buffer (could also use Redis for this)
short_term_memory = {}

# Connect to Redis
# redis_client = redis.StrictRedis(
#     host=Config.REDIS_HOST,  # Example: 'localhost'
#     port=Config.REDIS_PORT,  # Example: 6379
#     db=0,  # Default Redis DB
#     decode_responses=True  # Automatically decode responses from bytes to strings
# )

# def update_short_term_memory(user_id, new_message):
#     """
#     Stores the user's short-term memory in Redis.
#     Keeps the last 5 messages for each user.
#     """
#     key = f"user:{user_id}:short_term_memory"  # Key for this user's memory in Redis
    
#     # Add the new message to the user's memory list
#     redis_client.lpush(key, json.dumps(new_message))  # Store as JSON in Redis
    
#     # Limit the memory to the last 5 messages
#     redis_client.ltrim(key, 0, 4)  # Keep only the last 5 entries

# def get_short_term_memory(user_id):
#     """
#     Retrieves the user's short-term memory from Redis.
#     """
#     key = f"user:{user_id}:short_term_memory"
    
#     # Get the last 5 messages (or however many are available)
#     memory_list = redis_client.lrange(key, 0, 4)
    
#     # Convert JSON strings back into Python objects
#     return [json.loads(message) for message in memory_list]

# Function to store journal entry as embedding
def store_journal_embedding(user_id, journal_entry):
    # Generate embedding using OpenAI's embeddings API
    embedding = openai.Embedding.create(input=[journal_entry], model="text-embedding-ada-002")['data'][0]['embedding']
    
    # Store the embedding and journal entry in the database
    new_prompt = Prompts(user_id=user_id, prompt_text=journal_entry, embedding_vector=embedding)
    db.session.add(new_prompt)
    db.session.commit()

# TODO: Look into how to optimize this
# Function to retrieve relevant past journal entries using embeddings for both prompts and responses
def get_relevant_long_term_entries(user_id, query_text):
    # Generate embedding for the query
    query_embedding = openai.Embedding.create(input=[query_text], model="text-embedding-ada-002")['data'][0]['embedding']
    
    # Fetch past prompts and their associated responses from the database
    past_entries = db.session.query(Prompts, Responses).filter(Prompts.user_id == user_id, Prompts.prompt_id == Responses.prompt_id).all()

    similarities = []

    for prompt, response in past_entries:
        # Check if the embedding vectors are not None
        if prompt.embedding_vector is None or response.embedding_vector is None:
            continue  # Skip if embeddings are missing

        # Calculate cosine similarity for both prompt and response embeddings
        prompt_vector = np.array(prompt.embedding_vector)
        response_vector = np.array(response.embedding_vector)
        query_vector = np.array(query_embedding)

        # Cosine similarity between query and prompt
        prompt_similarity = np.dot(query_vector, prompt_vector) / (np.linalg.norm(query_vector) * np.linalg.norm(prompt_vector))

        # Cosine similarity between query and response
        response_similarity = np.dot(query_vector, response_vector) / (np.linalg.norm(query_vector) * np.linalg.norm(response_vector))

        # Combine prompt and response similarity (you could adjust this formula based on your needs)
        combined_similarity = (prompt_similarity + response_similarity) / 2

        similarities.append((prompt.prompt_text, response.response_text, combined_similarity))
    
    # Sort by combined similarity and return the top relevant entries (top 3 results)
    similarities.sort(key=lambda x: x[2], reverse=True)
    relevant_entries = [{"prompt": entry[0], "response": entry[1], "similarity": entry[2]} for entry in similarities[:3]]

    return relevant_entries

def generate_prompt_with_hybrid_memory(user_id, query_text):
    # Fetch recent messages from short-term memory
    # recent_context = get_short_term_memory(user_id)

    # Check if recent context or past entries are empty and provide a fallback
    # if not recent_context:
    #     recent_context = ["(No recent context available)"]

    # Fetch relevant past entries from long-term memory
    relevant_past_entries = get_relevant_long_term_entries(user_id, query_text)
        
    if not relevant_past_entries:
        relevant_past_entries = ["(No relevant past entries found)"]
    else:
        # Convert relevant past entries (which may be a list of dicts) to strings
        relevant_past_entries = [f"Prompt: {entry['prompt']}\nResponse: {entry['response']}" for entry in relevant_past_entries]

    # Combine the recent context and relevant past entries
    # combined_context = "Here’s what you’ve shared recently:\n" + "\n".join(recent_context) + "\n\n"
    combined_context = "Based on your previous journal entries:\n" + "\n".join(relevant_past_entries)

    # If both are empty, add a default message
    if combined_context.strip() == "":
        combined_context = "There is no previous context or entries available. You can start journaling now!"

    # Prepare the messages for the Chat Completion API
    messages = [
        {"role": "system", "content": "You are a journaling assistant that helps users generate personalized journal prompts based on their previous entries."},
        {"role": "user", "content": f"Here’s my context:\n{combined_context}\nPlease generate a new personalized journal prompt for me."}
    ]
    

    # Call OpenAI to generate the journal prompt based on combined context
    prompt_response = openai.ChatCompletion.create(
        model="gpt-4", 
        messages=messages,
        max_tokens=150
    )
    
    return prompt_response['choices'][0]['message']['content'].strip()


# Function to store journal entries in PostgreSQL using SQLAlchemy
# def store_journal_entry_in_db(user_id, journal_entry):
#     vector = openai.Embedding.create(input=[journal_entry], model=embedding_model)['data'][0]['embedding']
#     # Store the vector in PostgreSQL if needed or just store the entry text.
#     new_prompt = Prompts(user_id=user_id, prompt_text=journal_entry)
#     db.session.add(new_prompt)
#     db.session.commit()

# def process_user_journal(user_id, journal_entry):
#     # Update short-term memory with the new journal entry
#     update_short_term_memory(user_id, journal_entry)
    
#     # Store the journal entry in long-term memory using embeddings
#     store_journal_embedding(user_id, journal_entry)
    
#     # Generate a new prompt based on both short-term and long-term context
#     new_prompt = generate_prompt_with_hybrid_memory(user_id, journal_entry)
    
#     return new_prompt
