"""
Chat router with OpenAI-compatible streaming endpoint.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, AsyncGenerator, Union, Literal
from datetime import datetime
import json
import asyncio
import uuid
import time
import secrets
from sqlmodel import Session

from ..db import get_session, PersistenceRepository, ModeEnum
from ..services import client, get_default_model, get_ai_provider
from ..core.logging import get_logger
from .auth_router import get_optional_user
from ..db.models import User, ChatSummary, ChatHistoryResponse, ShareSettings, ShareResponse, SharedChatResponse
from ..core.anonymous_session import get_user_identifier

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["chat"])


# Request/Response models matching OpenAI's format
class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "function"]
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


class ChatCompletionRequest(BaseModel):
    model: str = Field(default_factory=get_default_model, description="Model to use for completion")
    messages: List[ChatMessage] = Field(..., description="List of messages in the conversation")
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1)
    n: Optional[int] = Field(default=1, ge=1, le=10)
    stream: Optional[bool] = Field(default=False)
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = Field(default=None, ge=1)
    presence_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    frequency_penalty: Optional[float] = Field(default=0, ge=-2, le=2)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    
    # Custom fields for our system
    chat_id: Optional[str] = Field(default=None, description="Chat session ID for persistence")
    save_to_db: Optional[bool] = Field(default=True, description="Whether to save to database")


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[ChatCompletionUsage] = None
    system_fingerprint: Optional[str] = None


class ChatCompletionChunkChoice(BaseModel):
    index: int
    delta: Dict[str, Any]
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionChunkChoice]
    system_fingerprint: Optional[str] = None


async def generate_streaming_response(
    request: ChatCompletionRequest,
    session: Session,
    http_request: Request,
    http_response: Response,
    current_user: Optional[User] = None
) -> AsyncGenerator[str, None]:
    """
    Generate streaming response compatible with OpenAI's SSE format.
    """
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"
    created_timestamp = int(time.time())
    full_response = ""
    error_occurred = False
    
    # Log AI provider being used
    logger.info(f"Using AI provider: {get_ai_provider()}, Model: {request.model}")
    
    try:
        # Create OpenAI streaming request
        stream = await client.chat.completions.create(
            model=request.model,
            messages=[msg.model_dump() for msg in request.messages],
            temperature=request.temperature,
            top_p=request.top_p,
            n=request.n,
            stream=True,
            stop=request.stop,
            max_tokens=request.max_tokens,
            presence_penalty=request.presence_penalty,
            frequency_penalty=request.frequency_penalty,
            logit_bias=request.logit_bias,
            user=request.user
        )
        
        # Stream chunks
        async for chunk in stream:
            try:
                # Convert OpenAI chunk to our format
                chunk_data = ChatCompletionChunk(
                    id=completion_id,
                    object="chat.completion.chunk",
                    created=created_timestamp,
                    model=request.model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=choice.index,
                            delta=choice.delta.model_dump() if choice.delta else {},
                            finish_reason=choice.finish_reason
                        )
                        for choice in chunk.choices
                    ],
                    system_fingerprint=chunk.system_fingerprint
                )
                
                # Accumulate response for database storage
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                
                # Send SSE formatted data
                yield f"data: {chunk_data.model_dump_json()}\n\n"
                
            except Exception as chunk_error:
                # Error processing individual chunk
                error_chunk = {
                    "error": {
                        "message": f"Chunk processing error: {str(chunk_error)}",
                        "type": "chunk_processing_error",
                        "code": "chunk_error"
                    }
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
                error_occurred = True
                break
        
        # Save to database if requested and no errors occurred
        if request.save_to_db and request.chat_id and not error_occurred:
            try:
                repository = PersistenceRepository(session)
                
                # Get the last user message as the question
                user_messages = [msg for msg in request.messages if msg.role == "user"]
                question = user_messages[-1].content if user_messages else ""
                
                # Get user identifier (authenticated user ID or anonymous session)
                user_identifier = get_user_identifier(current_user, http_request, http_response)
                
                chat = repository.create_chat(
                    chat_id=request.chat_id or f"chat_{uuid.uuid4().hex[:8]}",
                    message_id=completion_id,
                    question=question,
                    response=full_response,
                    mode=ModeEnum.single,
                    agents={"model": request.model, "streaming": True},
                    user_id=user_identifier
                )
            except Exception as db_error:
                # Database save error - send error but don't break the stream
                error_chunk = {
                    "error": {
                        "message": f"Database save error: {str(db_error)}",
                        "type": "database_error",
                        "code": "db_error"
                    }
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"
            
    except Exception as e:
        # General error (OpenAI API, network, etc.)
        error_chunk = {
            "error": {
                "message": str(e),
                "type": "streaming_error",
                "code": "internal_error"
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"
        error_occurred = True
    
    finally:
        # Always send [DONE] to signal stream completion, regardless of success or error
        yield "data: [DONE]\n\n"


@router.post("/chat/completions", response_model=None)
async def create_chat_completion(
    request: ChatCompletionRequest,
    http_request: Request,
    http_response: Response,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    OpenAI-compatible chat completion endpoint with streaming support.
    
    Example request:
    ```json
    {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ],
        "stream": true,
        "temperature": 0.7
    }
    ```
    """
    
    if request.stream:
        # Return streaming response
        return StreamingResponse(
            generate_streaming_response(request, session, http_request, http_response, current_user),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable Nginx buffering
            }
        )
    else:
        # Non-streaming response
        try:
            # Log AI provider being used
            logger.info(f"Using AI provider: {get_ai_provider()}, Model: {request.model}")
            
            completion = await client.chat.completions.create(
                model=request.model,
                messages=[msg.model_dump() for msg in request.messages],
                temperature=request.temperature,
                top_p=request.top_p,
                n=request.n,
                stream=False,
                stop=request.stop,
                max_tokens=request.max_tokens,
                presence_penalty=request.presence_penalty,
                frequency_penalty=request.frequency_penalty,
                logit_bias=request.logit_bias,
                user=request.user
            )
            
            # Save to database if requested
            if request.save_to_db and request.chat_id:
                repository = PersistenceRepository(session)
                
                # Get the last user message as the question
                user_messages = [msg for msg in request.messages if msg.role == "user"]
                question = user_messages[-1].content if user_messages else ""
                
                # Get the assistant's response
                response_content = completion.choices[0].message.content if completion.choices else ""
                
                # Get user identifier (authenticated user ID or anonymous session)
                user_identifier = get_user_identifier(current_user, http_request, http_response)
                
                chat = repository.create_chat(
                    chat_id=request.chat_id or f"chat_{uuid.uuid4().hex[:8]}",
                    message_id=completion.id,
                    question=question,
                    response=response_content,
                    mode=ModeEnum.single,
                    agents={"model": request.model, "streaming": False},
                    user_id=user_identifier
                )
            
            # Convert to our response format
            response = ChatCompletionResponse(
                id=completion.id,
                object="chat.completion",
                created=completion.created,
                model=completion.model,
                choices=[
                    ChatCompletionChoice(
                        index=choice.index,
                        message=ChatMessage(
                            role=choice.message.role,
                            content=choice.message.content
                        ),
                        finish_reason=choice.finish_reason
                    )
                    for choice in completion.choices
                ],
                usage=ChatCompletionUsage(
                    prompt_tokens=completion.usage.prompt_tokens,
                    completion_tokens=completion.usage.completion_tokens,
                    total_tokens=completion.usage.total_tokens
                ) if completion.usage else None,
                system_fingerprint=completion.system_fingerprint
            )
            
            return response
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error calling AI API: {str(e)}"
            )


@router.post("/chat/stream")
async def create_streaming_chat(
    request: ChatCompletionRequest,
    http_request: Request,
    http_response: Response,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
) -> StreamingResponse:
    """
    Explicit streaming endpoint that always returns SSE stream.
    
    This endpoint forces streaming regardless of the 'stream' parameter.
    """
    request.stream = True
    return StreamingResponse(
        generate_streaming_response(request, session, http_request, http_response, current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/chat/history/{chat_id}")
async def get_chat_history(
    chat_id: str,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
) -> List[Dict[str, Any]]:
    """
    Get chat history for a specific chat_id.
    If user is authenticated, only return their chats.
    """
    repository = PersistenceRepository(session)
    chats = repository.get_chat_by_id(chat_id)
    
    # Filter by user if authenticated
    if current_user:
        chats = [chat for chat in chats if chat.user_id == current_user.id]
    
    if not chats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No chat history found for chat_id: {chat_id}"
        )
    
    return [
        {
            "message_id": chat.message_id,
            "question": chat.question,
            "response": chat.response,
            "timestamp": chat.msg_timestamp.isoformat(),
            "mode": chat.mode.value,
            "agents": chat.agents
        }
        for chat in chats
    ]


@router.get("/models")
async def list_models() -> Dict[str, Any]:
    """
    List available models (OpenAI-compatible endpoint).
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-3.5-turbo",
                "object": "model",
                "created": 1677610602,
                "owned_by": "openai",
                "permission": [],
                "root": "gpt-3.5-turbo",
                "parent": None
            },
            {
                "id": "gpt-4",
                "object": "model",
                "created": 1687882411,
                "owned_by": "openai",
                "permission": [],
                "root": "gpt-4",
                "parent": None
            },
            {
                "id": "gpt-4-turbo-preview",
                "object": "model",
                "created": 1706745304,
                "owned_by": "openai",
                "permission": [],
                "root": "gpt-4-turbo-preview",
                "parent": None
            }
        ]
    }


# Chat History Management endpoints
class ChatTitleUpdate(BaseModel):
    """Model for updating chat title."""
    title: str = Field(..., min_length=1, max_length=255)


@router.get("/chats", response_model=List[ChatSummary])
async def get_all_chats(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get all chat sessions for the current user.
    Supports pagination and search functionality.
    """
    repository = PersistenceRepository(session)
    
    # Get user_id if authenticated, otherwise None for anonymous chats
    user_id = str(current_user.id) if current_user else None
    
    chats = repository.get_all_chats(
        user_id=user_id,
        limit=limit,
        offset=offset,
        search_query=search
    )
    
    return chats


@router.get("/chat/{chat_id}/full", response_model=ChatHistoryResponse)
async def get_full_chat_history(
    chat_id: str,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get full chat history with all messages for a specific chat.
    """
    repository = PersistenceRepository(session)
    
    # Get user_id if authenticated, otherwise None for anonymous chats
    user_id = str(current_user.id) if current_user else None
    
    chat_history = repository.get_chat_history_with_messages(chat_id, user_id)
    
    if not chat_history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat history not found for chat_id: {chat_id}"
        )
    
    return chat_history


@router.delete("/chat/{chat_id}")
async def delete_chat_history(
    chat_id: str,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Delete (soft delete) a chat session and all its messages.
    """
    repository = PersistenceRepository(session)
    
    # Get user_id if authenticated, otherwise None for anonymous chats
    user_id = str(current_user.id) if current_user else None
    
    success = repository.delete_chat(chat_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat not found for chat_id: {chat_id}"
        )
    
    return {"message": f"Chat {chat_id} deleted successfully"}


@router.put("/chat/{chat_id}/title")
async def update_chat_title(
    chat_id: str,
    title_update: ChatTitleUpdate,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Update the title of a chat session.
    """
    repository = PersistenceRepository(session)
    
    # Get user_id if authenticated, otherwise None for anonymous chats
    user_id = str(current_user.id) if current_user else None
    
    success = repository.update_chat_title(chat_id, title_update.title, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat not found for chat_id: {chat_id}"
        )
    
    return {"message": f"Chat title updated successfully", "title": title_update.title}


@router.get("/chat/{chat_id}/summary", response_model=ChatSummary)
async def get_chat_summary(
    chat_id: str,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get summary information for a specific chat.
    """
    repository = PersistenceRepository(session)
    
    # Get user_id if authenticated, otherwise None for anonymous chats
    user_id = str(current_user.id) if current_user else None
    
    summary = repository.get_chat_summary(chat_id, user_id)
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat not found for chat_id: {chat_id}"
        )
    
    return summary


# Share endpoints
@router.post("/chat/{chat_id}/share", response_model=ShareResponse)
async def share_chat(
    chat_id: str,
    settings: ShareSettings,
    request: Request,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Share a chat publicly with custom settings.
    Only the chat owner can share their chat.
    """
    repository = PersistenceRepository(session)
    
    # Must be authenticated to share
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to share chats"
        )
    
    # Verify the user owns this chat
    user_id = str(current_user.id)
    chat_messages = repository.get_chat_by_id(chat_id)
    
    if not chat_messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if any message belongs to the user
    user_owns_chat = any(msg.user_id == user_id for msg in chat_messages)
    if not user_owns_chat:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only share your own chats"
        )
    
    # Check if already shared
    existing_share = repository.get_shared_chat_by_chat_id(chat_id, user_id)
    if existing_share:
        # Update existing share
        updated_share = repository.update_shared_chat(chat_id, user_id, settings)
        if not updated_share:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update share settings"
            )
        
        # Generate share URL
        base_url = str(request.base_url).rstrip('/')
        share_url = f"{base_url}/shared/{updated_share.share_token}"
        
        return ShareResponse(
            share_token=updated_share.share_token,
            share_url=share_url,
            title=updated_share.title,
            is_public=updated_share.is_public,
            expires_at=updated_share.expires_at,
            created_at=updated_share.created_at
        )
    
    # Generate secure share token
    share_token = secrets.token_urlsafe(32)
    
    # Create new shared chat
    shared_chat = repository.create_shared_chat(share_token, chat_id, user_id, settings)
    
    # Generate share URL
    base_url = str(request.base_url).rstrip('/')
    share_url = f"{base_url}/shared/{share_token}"
    
    return ShareResponse(
        share_token=share_token,
        share_url=share_url,
        title=shared_chat.title,
        is_public=shared_chat.is_public,
        expires_at=shared_chat.expires_at,
        created_at=shared_chat.created_at
    )


@router.get("/shared/{share_token}", response_model=SharedChatResponse)
async def get_shared_chat(
    share_token: str,
    session: Session = Depends(get_session)
):
    """
    Get a shared chat by its token.
    Public endpoint - no authentication required.
    """
    repository = PersistenceRepository(session)
    
    # Get shared chat info
    shared_chat = repository.get_shared_chat_by_token(share_token)
    if not shared_chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared chat not found or has expired"
        )
    
    # Get chat messages
    chat_messages = repository.get_chat_by_id(shared_chat.chat_id)
    if not chat_messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original chat not found"
        )
    
    # Increment view count
    repository.increment_view_count(share_token)
    
    # Format messages
    formatted_messages = []
    for msg in chat_messages:
        if not msg.is_deleted:  # Only include non-deleted messages
            formatted_messages.append({
                "message_id": msg.message_id,
                "question": msg.question,
                "response": msg.response,
                "timestamp": msg.msg_timestamp.isoformat(),
                "mode": msg.mode.value,
                "agents": msg.agents
            })
    
    # Sort by timestamp
    formatted_messages.sort(key=lambda x: x["timestamp"])
    
    return SharedChatResponse(
        share_token=share_token,
        chat_id=shared_chat.chat_id,
        title=shared_chat.title,
        description=shared_chat.description,
        is_public=shared_chat.is_public,
        view_count=shared_chat.view_count,
        created_at=shared_chat.created_at,
        messages=formatted_messages
    )


@router.delete("/chat/{chat_id}/share")
async def unshare_chat(
    chat_id: str,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Remove sharing for a chat (make it private again).
    Only the chat owner can unshare their chat.
    """
    repository = PersistenceRepository(session)
    
    # Must be authenticated to unshare
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to unshare chats"
        )
    
    user_id = str(current_user.id)
    
    # Verify the user owns this chat
    chat_messages = repository.get_chat_by_id(chat_id)
    if not chat_messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if any message belongs to the user
    user_owns_chat = any(msg.user_id == user_id for msg in chat_messages)
    if not user_owns_chat:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only unshare your own chats"
        )
    
    # Delete the share
    success = repository.delete_shared_chat(chat_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat is not currently shared"
        )
    
    return {"message": "Chat unshared successfully"}


@router.get("/chat/{chat_id}/share", response_model=ShareResponse)
async def get_chat_share_info(
    chat_id: str,
    request: Request,
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get share information for a chat if it's currently shared.
    Only the chat owner can view share info.
    """
    repository = PersistenceRepository(session)
    
    # Must be authenticated
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    user_id = str(current_user.id)
    
    # Verify the user owns this chat
    chat_messages = repository.get_chat_by_id(chat_id)
    if not chat_messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Check if any message belongs to the user
    user_owns_chat = any(msg.user_id == user_id for msg in chat_messages)
    if not user_owns_chat:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view share info for your own chats"
        )
    
    # Get share info
    shared_chat = repository.get_shared_chat_by_chat_id(chat_id, user_id)
    if not shared_chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat is not currently shared"
        )
    
    # Generate share URL
    base_url = str(request.base_url).rstrip('/')
    share_url = f"{base_url}/shared/{shared_chat.share_token}"
    
    return ShareResponse(
        share_token=shared_chat.share_token,
        share_url=share_url,
        title=shared_chat.title,
        is_public=shared_chat.is_public,
        expires_at=shared_chat.expires_at,
        created_at=shared_chat.created_at
    )