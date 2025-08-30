"""
Chat router with OpenAI-compatible streaming endpoint.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, AsyncGenerator, Union, Literal
from datetime import datetime
import json
import asyncio
import uuid
import time
from sqlmodel import Session

from ..db import get_session, PersistenceRepository, ModeEnum
from ..services import client, get_default_model, get_ai_provider
from ..core.logging import get_logger
from .auth_router import get_optional_user
from ..db.models import User

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
                
                chat = repository.create_chat(
                    chat_id=request.chat_id or f"chat_{uuid.uuid4().hex[:8]}",
                    message_id=completion_id,
                    question=question,
                    response=full_response,
                    mode=ModeEnum.single,
                    agents={"model": request.model, "streaming": True}
                )
                # Update chat with user_id if authenticated
                if current_user:
                    chat.user_id = current_user.id
                    session.add(chat)
                    session.commit()
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
            generate_streaming_response(request, session, current_user),
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
                
                chat = repository.create_chat(
                    chat_id=request.chat_id or f"chat_{uuid.uuid4().hex[:8]}",
                    message_id=completion.id,
                    question=question,
                    response=response_content,
                    mode=ModeEnum.single,
                    agents={"model": request.model, "streaming": False}
                )
                # Update chat with user_id if authenticated
                if current_user:
                    chat.user_id = current_user.id
                    session.add(chat)
                    session.commit()
            
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
    session: Session = Depends(get_session)
) -> StreamingResponse:
    """
    Explicit streaming endpoint that always returns SSE stream.
    
    This endpoint forces streaming regardless of the 'stream' parameter.
    """
    request.stream = True
    return StreamingResponse(
        generate_streaming_response(request, session),
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