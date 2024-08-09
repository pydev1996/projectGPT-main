import datetime
import re
import shelve
import time
from openai import OpenAI
from app.config import settings
from app.database import get_database
from motor.motor_asyncio import AsyncIOMotorCollection
    
client = OpenAI(api_key=settings.OPEN_AI_API_KEY)
def get_assistant_by_id(assistant_id: str):
    assistant = client.beta.assistants.retrieve(assistant_id)
    return assistant

'''
def create_assistant(assistant):
    """
    You currently cannot set the temperature for Assistant via the API.
    """
    assistant = client.beta.assistants.create(
        name=assistant.name,
        instructions=assistant.instructions,
        tools=[{"type": "retrieval"}],
        model="gpt-4-1106-preview",
        file_ids=[file.id],
    )
    return assistant
'''



async def check_if_thread_exists(conv_id, assistant_id):
    db = get_database()
    gptconversations: AsyncIOMotorCollection = db['gptconversations']

    # querying database to check if user already exists
    thread = await gptconversations.find_one({"conv_id": conv_id, "assistant_id": assistant_id})
    if thread:
        return thread['thread_id']
    else:
        return None
    
async def remove_if_thread_exists(conv_id, assistant_id):
    db = get_database()
    gptconversations: AsyncIOMotorCollection = db['gptconversations']
    # Check if the thread exists
    existing_thread = await gptconversations.find_one({"conv_id": conv_id, "assistant_id": assistant_id})

    if existing_thread:
        # Thread exists, remove it
        await gptconversations.update_one(
            {"_id": existing_thread["_id"]},
            {"$set": {"status": "deleted"}}
        )
        return True
    else:
        print(f"No thread found for conv_id: {conv_id}, assistant_id: {assistant_id}.")
        return False


async def store_thread(conv_id, assistant_id, thread_id, title, user_id):
    db = get_database()
    gptconversations: AsyncIOMotorCollection = db['gptconversations']

    # querying database to check if user already exists
    thread = {
        'conv_id': conv_id,
        'thread_id': thread_id,
        'assistant_id': assistant_id,
        'title': title,
        'user_id': user_id,
        'created_at': datetime.datetime.now(),
        'updated_at': datetime.datetime.now(),
        'status': 'active'
    }

    result = await gptconversations.insert_one(thread)
    thread["_id"] = result.inserted_id
    return thread
        
        
async def create_and_store_thread(conv_id, assistant_id, title, user_id):
    # Create a new thread
    thread = client.beta.threads.create()

    # Store the thread
    return await store_thread(conv_id, assistant_id, thread.id, title, user_id)

async def generate_response(message_body, conv_id, email, assistant_id):
    # Check if there is already a thread_id for the conv_id
    thread_id = await check_if_thread_exists(conv_id, assistant_id)

    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        raise Exception("No thread found for conv_id: {conv_id}, assistant_id: {assistant_id}.")

    # Otherwise, retrieve the existing thread
    # else:
    #     print(f"Retrieving existing thread for {email} with conv_id {conv_id}")
    #     thread = client.beta.threads.retrieve(thread_id)
    #     thread_id = thread.id

    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )

    # Run the assistant and get the new message
    messages = await run_assistant(thread_id, assistant_id)
    new_message = messages.data[0].content[0].text.value
    return new_message


async def run_assistant(thread_id, assistant_id):

    # Run the assistant
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id,
        additional_instructions="Ask only one question at a time for clarifications."
    )

    # # Wait for completion
    # while run.status != "completed":
    #     # Be nice to the API
    #     time.sleep(0.5)
    #     run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )
        return messages
    else:
        print(run.status)
        return messages
    

async def fetch_messages(thread_id):
    messages = client.beta.threads.messages.list(
        thread_id=thread_id
    )
    return messages

async def getConversationCountForToday(user):
    db = get_database()
    gptconversations: AsyncIOMotorCollection = db['gptconversations']
    current_date = datetime.datetime.now().date().isoformat()
    conversations = await gptconversations.find({"user_id": str(user['_id'])}).to_list(length=None)
    conversations_count = 0
    for conversation in conversations:
        if conversation['created_at'].date().isoformat() == current_date:
            conversations_count += 1
    return conversations_count


async def extract_skills_from_paragraph(paragraph: str, assistant_id):
    # Use OpenAI's completion API to extract skills
    thread = client.beta.threads.create()
    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=paragraph,
    )

    # Run the assistant
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )
    #additional_instructions=f"Keep the technical skills with the same spelling as mentioned in {availableSkills}"


    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        return extract_title_and_skills(messages.data[0].content[0].text.value)
    else:
        print(run.status)
        raise Exception("Could not extract skills from paragraph from OpenAI.")

def extract_title_and_skills(text):
    # Extract the title
    title_search = re.search(r"Title:\s*(.+)", text)
    title = title_search.group(1).strip() if title_search else None
    
    # Extract the technical skills
    skills_search = re.search(r"Technical Skills:\s*(.+)", text)
    skills = skills_search.group(1).strip().split(", ") if skills_search else []

    return title, skills

async def update_emailsend_for_conv(conv_id):
    db = get_database()
    gptconversations: AsyncIOMotorCollection = db['gptconversations']
    await gptconversations.update_one(
        {"conv_id": conv_id},
        {"$set": {"emailsend": True}}
    )