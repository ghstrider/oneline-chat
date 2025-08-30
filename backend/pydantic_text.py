from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import json


class ContentItem(BaseModel):
    type: str = Field(..., description="Content type, e.g., 'output_text'")
    text: str = Field(..., description="The actual text content")


class OutputItem(BaseModel):
    content: List[ContentItem] = Field(..., description="List of content items")


class ChatDataStructure(BaseModel):
    output: List[OutputItem] = Field(..., description="List of output items")


class ChatRecord(BaseModel):
    response: str = Field(..., description="The response text from the chat", min_length=1)
    chat_data: Optional[ChatDataStructure] = Field(default=None)
    timestamp: Optional[datetime] = Field(default=None)

    @field_validator("chat_data", mode="before")
    @classmethod
    def parse_chat_data_json(cls, v):
        """Parse stringified JSON chat_data."""
        if isinstance(v, str) and v.strip():
            try:
                parsed_data = json.loads(v)
                if isinstance(parsed_data, dict) and "output" in parsed_data:
                    return ChatDataStructure(**parsed_data)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Failed to parse chat_data: {e}")
                return None
        return v

    @model_validator(mode="after")
    def extract_response_from_chat_data(self):
        """Extract text from chat_data and update response after model is built."""
        if self.chat_data is not None:
            extracted_texts = []
            for output_item in self.chat_data.output:
                for content_item in output_item.content:
                    if content_item.type == "output_text":
                        extracted_texts.append(content_item.text)

            if extracted_texts:
                # Create a new instance with updated response
                object.__setattr__(self, "response", " ".join(extracted_texts))

        return self

    @property
    def extracted_texts(self) -> List[str]:
        """Get all extracted text content."""
        if self.chat_data is None:
            return []

        texts = []
        for output_item in self.chat_data.output:
            for content_item in output_item.content:
                if content_item.type == "output_text":
                    texts.append(content_item.text)
        return texts


# Example usage
if __name__ == "__main__":
    stringified_chat_data = '{"output":[{"content":[{"type":"output_text","text":"Hello World"}]}]}'

    record = ChatRecord(response="placeholder", chat_data=stringified_chat_data)

    print(f"Response: '{record.response}'")  # "Hello World"
    print(f"Extracted: {record.extracted_texts}")  # ["Hello World"]
