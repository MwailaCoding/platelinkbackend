# tests/test_ai_menu_extraction.py
import os
# Set mock key for testing before any app modules are imported
os.environ["OPENAI_API_KEY"] = "mock_api_key_for_testing"

import pytest
import base64
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from decimal import Decimal

from app.services.openai_menu_extractor import OpenAIMenuExtractor
from app.api.v1.routes.menu_ai import router

from openai import RateLimitError, APIError

# Sample fixtures
SAMPLE_MENU_JSON = {
    "categories": [
        {
            "name": "Drinks",
            "items": [
                {"name": "Cold Soda", "price": 150.00, "description": "300ml bottle"}
            ]
        }
    ],
    "confidence": 0.95
}

class MockChoiceMessage:
    def __init__(self, content: str):
        self.content = content

class MockChoice:
    def __init__(self, content: str):
        self.message = MockChoiceMessage(content)

class MockUsage:
    def __init__(self, prompt_tokens: int, completion_tokens: int, total_tokens: int):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens

class MockChatCompletionResponse:
    def __init__(self, content_str: str, prompt: int = 100, completion: int = 50, total: int = 150):
        self.choices = [MockChoice(content_str)]
        self.usage = MockUsage(prompt, completion, total)

@pytest.mark.asyncio
async def test_extract_from_jpeg_success():
    """
    Test successful extraction from a JPEG image using mock OpenAI response.
    """
    extractor = OpenAIMenuExtractor()
    dummy_image = b"fake_jpeg_bytes"
    mock_response_str = '{"categories": [{"name": "Drinks", "items": [{"name": "Soda", "price": 150.00, "description": "Cold"}]}], "confidence": 0.95}'
    
    mock_response = MockChatCompletionResponse(mock_response_str, prompt=200, completion=100, total=300)
    
    with patch.object(extractor.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        
        result = await extractor.extract_from_image(dummy_image, "menu.jpg")
        
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["confidence"] == 0.95
        assert result["usage"]["total_tokens"] == 300
        assert result["usage"]["estimated_cost_usd"] > 0
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_extract_from_png_success():
    """
    Test successful extraction from a PNG image using mock OpenAI response.
    """
    extractor = OpenAIMenuExtractor()
    dummy_image = b"fake_png_bytes"
    mock_response_str = '{"categories": [{"name": "Starters", "items": [{"name": "Samosa", "price": 300.00, "description": "Beef"}]}], "confidence": 0.90}'
    
    mock_response = MockChatCompletionResponse(mock_response_str, prompt=150, completion=80, total=230)
    
    with patch.object(extractor.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        
        result = await extractor.extract_from_image(dummy_image, "menu.png")
        
        assert result["success"] is True
        assert result["data"]["categories"][0]["name"] == "Starters"
        assert result["usage"]["total_tokens"] == 230
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_extract_from_pdf_success():
    """
    Test successful extraction from a PDF document by mocking page conversion and vision requests.
    """
    extractor = OpenAIMenuExtractor()
    dummy_pdf = b"fake_pdf_bytes"
    
    # 2 pages of dummy images
    dummy_images = [b"page1_bytes", b"page2_bytes"]
    
    page1_response_str = '{"categories": [{"name": "Drinks", "items": [{"name": "Water", "price": 100.0}]}], "confidence": 0.95}'
    page2_response_str = '{"categories": [{"name": "Desserts", "items": [{"name": "Cake", "price": 350.0}]}], "confidence": 0.85}'
    
    mock_response_page1 = MockChatCompletionResponse(page1_response_str, prompt=100, completion=50, total=150)
    mock_response_page2 = MockChatCompletionResponse(page2_response_str, prompt=100, completion=50, total=150)
    
    with patch("app.services.openai_menu_extractor.convert_pdf_to_images") as mock_convert, \
         patch.object(extractor.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
         
        mock_convert.return_value = dummy_images
        mock_create.side_effect = [mock_response_page1, mock_response_page2]
        
        result = await extractor.extract_from_pdf(dummy_pdf)
        
        assert result["success"] is True
        assert len(result["data"]["categories"]) == 2
        # Verify both page responses are merged
        cat_names = [cat["name"] for cat in result["data"]["categories"]]
        assert "Drinks" in cat_names
        assert "Desserts" in cat_names
        # Validate accumulated token usage
        assert result["usage"]["total_tokens"] == 300
        assert result["data"]["confidence"] == 0.90 # average of 0.95 and 0.85

@pytest.mark.asyncio
async def test_extract_invalid_file_type():
    """
    Test that invalid file extensions are correctly filtered out at the endpoint level.
    """
    from fastapi import HTTPException
    # Mocking standard inputs
    from app.api.v1.routes.menu_ai import ai_extract_menu
    
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "unsupported.txt"
    mock_file.content_type = "text/plain"
    # Return mock content less than 20MB
    mock_file.read = AsyncMock(return_value=b"plain text content")
    
    mock_user = MagicMock()
    mock_db = AsyncMock()
    
    with pytest.raises(HTTPException) as exc_info:
        await ai_extract_menu(file=mock_file, current_user=mock_user, db=mock_db)
        
    assert exc_info.value.status_code == 400
    assert "Unsupported file type" in exc_info.value.detail

@pytest.mark.asyncio
async def test_extract_file_too_large():
    """
    Test that uploading files larger than 20MB triggers a file size limit exception.
    """
    from app.api.v1.routes.menu_ai import ai_extract_menu, MAX_FILE_SIZE_BYTES
    
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "large_menu.jpg"
    mock_file.content_type = "image/jpeg"
    # Mock read returning content larger than MAX_FILE_SIZE_BYTES
    mock_file.read = AsyncMock(return_value=b"a" * (MAX_FILE_SIZE_BYTES + 100))
    
    mock_user = MagicMock()
    mock_db = AsyncMock()
    
    with pytest.raises(HTTPException) as exc_info:
        await ai_extract_menu(file=mock_file, current_user=mock_user, db=mock_db)
        
    assert exc_info.value.status_code == 400
    assert "File is too large" in exc_info.value.detail

@pytest.mark.asyncio
async def test_extract_rate_limit_handling():
    """
    Test that OpenAI Rate Limit Errors are captured and handled gracefully.
    """
    extractor = OpenAIMenuExtractor()
    dummy_image = b"fake_bytes"
    
    mock_request = MagicMock()
    # Mocking a RateLimitError
    rate_limit_error = RateLimitError(
        message="Rate limit exceeded",
        response=MagicMock(),
        body={}
    )
    
    with patch.object(extractor.client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = rate_limit_error
        
        result = await extractor.extract_from_image(dummy_image, "menu.jpg")
        
        assert result["success"] is False
        assert "Rate limit exceeded" in result["error"]
