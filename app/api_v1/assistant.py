from app.config import settings
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_database
from app.schemas import Assistant, ConvMessages, Conversation, GenerateResponseInput, TokenSchema, User, UserAuth, UserOut
from app.utils import create_access_token, create_refresh_token, get_hashed_password, verify_password
from uuid import uuid4
from app.deps import get_current_user
from motor.motor_asyncio import AsyncIOMotorCollection
from app import helperAI
from typing import List
import re 

assistant_router = APIRouter()

@assistant_router.get("/assistant/get/{assistant_id}",response_model=Assistant)
async def get_assistant(assistant_id: str, user: User = Depends(get_current_user)):
    assistant = helperAI.get_assistant_by_id(assistant_id)
    if assistant is None:
        raise HTTPException(status_code=404, detail="Assistant not found")
    return assistant

@assistant_router.post("/generate_response")
async def get_ai_response(input_data: GenerateResponseInput, user: User = Depends(get_current_user)):
    try:
        new_message = await helperAI.generate_response(input_data.message_body, input_data.conv_id, user['email'], settings.PROJECT_ASSISTANT_ID)
        return new_message
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@assistant_router.post("/create/conversation_id", response_model=Conversation)
async def create_conv_id(title: str, user: User = Depends(get_current_user)):
    # Count the number of conversations initiated on the current date
    conversations_count = await helperAI.getConversationCountForToday(user)

    # If the number of conversations initiated on the current date is greater than 5, return an error
    if conversations_count > 4:
        raise HTTPException(status_code=429, detail="Maximum session reached for the day")
    try:
        conv_id = str(uuid4())
        # Check if there is already a thread_id for the conv_id
        thread_id = await helperAI.check_if_thread_exists(conv_id, settings.PROJECT_ASSISTANT_ID)
        
        # If a thread doesn't exist, create one and store it
        if thread_id is None:
            return await helperAI.create_and_store_thread(conv_id, settings.PROJECT_ASSISTANT_ID, title, str(user['_id']))
        else:
            raise HTTPException(status_code=409, detail="Already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@assistant_router.get("/conversation/history", response_model=List[Conversation])
async def get_conversations(user: User = Depends(get_current_user)):
    try:
        db = get_database()
        gptconversations: AsyncIOMotorCollection = db['gptconversations']
        conversations = await gptconversations.find({"user_id": str(user['_id']), "status":"active"}).to_list(length=50)
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@assistant_router.get("/conversation/history/search/{search_term}", response_model=List[Conversation])
async def search_conversations(search_term: str, user: User = Depends(get_current_user)):
    try:
        db = get_database()
        gptconversations: AsyncIOMotorCollection = db['gptconversations']
        conversations = await gptconversations.find({"user_id": str(user['_id']), "status":"active",  "title": {"$regex": re.compile(search_term, re.IGNORECASE)}}).to_list(length=50)
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@assistant_router.get("/conversation/{conv_id}/messages", response_model=List[ConvMessages])
async def get_messages(conv_id: str, user: User = Depends(get_current_user)):
    try:
        db = get_database()
        gptconversations: AsyncIOMotorCollection = db['gptconversations']
        conversation = await gptconversations.find_one({"conv_id": conv_id})
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages =await helperAI.fetch_messages(conversation['thread_id'])
        output_messages = []
        if messages is None:
            raise HTTPException(status_code=404, detail="No messages found for this thread")
        for message in messages.data:
            content = []
            for msg in message.content:
                content.append({"text": msg.text.value, "type": msg.type})
            role = message.role
            created_at = message.created_at
            output_messages.append({"content": content, "role": role, "created_at": created_at})
        output_messages.reverse()
        return output_messages
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@assistant_router.delete("/thread/{conv_id}")
async def delete_thread(conv_id: str, user: User = Depends(get_current_user)):
    try:
        return await helperAI.remove_if_thread_exists(conv_id, settings.PROJECT_ASSISTANT_ID)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))