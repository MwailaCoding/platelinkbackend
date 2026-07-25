# app/services/openai_menu_extractor.py
import os
import base64
import json
import logging
import time
import mimetypes
from typing import List, Dict, Any
from openai import AsyncOpenAI, APIError
from app.services.pdf_converter import convert_pdf_to_images
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

class OpenAIMenuExtractor:
    def __init__(self):
        # Read configuration values from Central settings (loaded via Pydantic from .env)
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.timeout = float(settings.AI_EXTRACTION_TIMEOUT_SECONDS)

        if not self.api_key or self.api_key == "your_actual_api_key_here":
            logger.warning("OPENAI_API_KEY environment variable is not set or is a placeholder. OpenAI calls will fail.")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=self.api_key)



    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculates estimated cost in USD based on gpt-4o-mini pricing:
        - Input: $0.150 per 1M tokens ($0.00000015 per token)
        - Output: $0.600 per 1M tokens ($0.00000060 per token)
        """
        input_cost = (prompt_tokens * 0.15) / 1_000_000.0
        output_cost = (completion_tokens * 0.60) / 1_000_000.0
        return round(input_cost + output_cost, 6)

    def _get_mime_type(self, filename: str) -> str:
        """Helper to determine MIME type from filename extension."""
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type in ["image/jpeg", "image/png"]:
            return mime_type
        # Fallback default
        if filename.lower().endswith(".png"):
            return "image/png"
        return "image/jpeg"

    async def extract_from_image(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Converts an image into base64, submits it to GPT-4o-mini vision model,
        and parses out structured categories, items, prices, and descriptions.
        """
        start_time = time.time()
        if not self.client:
            return {"success": False, "error": "OpenAI API Client is not configured. Set a valid OPENAI_API_KEY in the environment."}

        try:
            # Base64 encode the image
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            media_type = self._get_mime_type(filename)
            
            prompt = (
                "You are an expert restaurant menu digitizer. Analyze the provided menu image and extract "
                "all categories, items, prices, and descriptions. For each menu item:\n"
                "1. Clean the price to be a numeric float/integer representing KES (Kenya Shillings). "
                "Strip currency signs, commas, or letters (e.g. 'KES 650/=' becomes 650.00). If the price is not visible, "
                "missing, or free, set it to 0.0.\n"
                "2. Keep the item name exact. Extract descriptions if available; otherwise, set to null.\n"
                "3. Classify items under their correct category name (e.g., 'Starters', 'Drinks', 'Main Course').\n"
                "4. Estimate your extraction confidence score between 0.0 (low) and 1.0 (high) based on image readability.\n\n"
                "Return ONLY a valid JSON object matching the following structure:\n"
                "{\n"
                '  "categories": [\n'
                "    {\n"
                '      "name": "Category Name",\n'
                '      "items": [\n'
                '        {"name": "Item Name", "price": 450.00, "description": "Item description or null"}\n'
                "      ]\n"
                "    }\n"
                "  ],\n"
                '  "confidence": 0.95\n'
                "}"
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )

            # Parse response
            content_str = response.choices[0].message.content
            data = json.loads(content_str)

            # Token tracking
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            estimated_cost = self._calculate_cost(prompt_tokens, completion_tokens)
            processing_time_ms = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "data": data,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost_usd": estimated_cost
                },
                "processing_time_ms": processing_time_ms
            }

        except APIError as api_err:
            logger.error(f"OpenAI API error extracting menu from image: {str(api_err)}", exc_info=True)
            return {"success": False, "error": f"OpenAI Service error: {api_err.message}"}
        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to decode JSON from OpenAI response: {str(json_err)}", exc_info=True)
            return {"success": False, "error": "AI returned malformed JSON response. Please try again."}
        except Exception as e:
            logger.error(f"Unexpected error in extract_from_image: {str(e)}", exc_info=True)
            return {"success": False, "error": f"System error: {str(e)}"}

    async def extract_from_text(self, text: str) -> Dict[str, Any]:
        """
        Fallback method to parse raw text or OCR output into structured menu JSON using GPT-4o-mini.
        """
        start_time = time.time()
        if not self.client:
            return {"success": False, "error": "OpenAI API Client is not configured. Set a valid OPENAI_API_KEY in the environment."}

        try:
            prompt = (
                "You are an expert restaurant menu parser. Analyze the following menu text and extract "
                "all categories, items, prices, and descriptions. For each menu item:\n"
                "1. Clean the price to be a numeric float/integer representing KES (Kenya Shillings). "
                "Strip currency signs, commas, or letters (e.g. 'KES 650/=' becomes 650.00). If the price is not visible, "
                "missing, or free, set it to 0.0.\n"
                "2. Keep the item name exact. Extract descriptions if available; otherwise, set to null.\n"
                "3. Classify items under their correct category name (e.g., 'Starters', 'Drinks', 'Main Course').\n"
                "4. Estimate your extraction confidence score between 0.0 and 1.0.\n\n"
                "Menu Text:\n"
                f"{text}\n\n"
                "Return ONLY a valid JSON object matching the structure:\n"
                "{\n"
                '  "categories": [\n'
                "    {\n"
                '      "name": "Category Name",\n'
                '      "items": [\n'
                '        {"name": "Item Name", "price": 450.00, "description": "Item description or null"}\n'
                "      ]\n"
                "    }\n"
                "  ],\n"
                '  "confidence": 0.90\n'
                "}"
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )

            content_str = response.choices[0].message.content
            data = json.loads(content_str)

            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            estimated_cost = self._calculate_cost(prompt_tokens, completion_tokens)
            processing_time_ms = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "data": data,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost_usd": estimated_cost
                },
                "processing_time_ms": processing_time_ms
            }

        except APIError as api_err:
            logger.error(f"OpenAI API error extracting menu from text: {str(api_err)}", exc_info=True)
            return {"success": False, "error": f"OpenAI Service error: {api_err.message}"}
        except json.JSONDecodeError:
            return {"success": False, "error": "AI returned malformed JSON response. Please try again."}
        except Exception as e:
            logger.error(f"Unexpected error in extract_from_text: {str(e)}", exc_info=True)
            return {"success": False, "error": f"System error: {str(e)}"}

    async def extract_from_pdf(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Converts all PDF pages into images using pdf_converter, extracts each page
        separately, and merges the category and item records atomically.
        """
        start_time = time.time()
        
        # Convert pages to images
        images = convert_pdf_to_images(pdf_bytes)
        if not images:
            return {"success": False, "error": "Failed to convert PDF to images. Ensure the PDF is not corrupted and Poppler is installed."}

        results = []
        for i, img_bytes in enumerate(images):
            # Process each page using the vision model
            filename = f"page_{i + 1}.png"
            page_res = await self.extract_from_image(img_bytes, filename)
            if page_res.get("success"):
                results.append(page_res)
            else:
                logger.warning(f"Failed to extract text from page {i + 1} of PDF: {page_res.get('error')}")

        if not results:
            return {"success": False, "error": "Could not extract menu items from any pages of the PDF."}

        # Merge extracted categories and details
        merged_data = self._merge_extracted_menus(results)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        merged_data["processing_time_ms"] = processing_time_ms

        return merged_data

    def _merge_extracted_menus(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregates results from multiple pages:
        - Groups categories case-insensitively, merges their items.
        - Deduplicates items in the same category based on lowercase item name.
        - Sums up token usages and costs.
        - Averages confidence score.
        """
        categories_map: Dict[str, Dict[str, Any]] = {}
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0
        total_cost = 0.0
        confidences = []

        for res in results:
            data = res.get("data", {})
            usage = res.get("usage", {})
            
            # Sum tokens and costs
            total_prompt_tokens += usage.get("prompt_tokens", 0)
            total_completion_tokens += usage.get("completion_tokens", 0)
            total_tokens += usage.get("total_tokens", 0)
            total_cost += usage.get("estimated_cost_usd", 0.0)
            
            if "confidence" in data:
                confidences.append(float(data["confidence"]))

            # Parse categories
            for cat in data.get("categories", []):
                cat_name = cat.get("name", "").strip()
                if not cat_name:
                    continue
                
                # Check for case-insensitive match
                matched_key = None
                for key in categories_map.keys():
                    if key.lower() == cat_name.lower():
                        matched_key = key
                        break
                
                if matched_key:
                    # Merge items into existing category
                    for item in cat.get("items", []):
                        item_name = item.get("name", "").strip()
                        if not item_name:
                            continue
                        # Check if item name already exists in this category
                        item_exists = any(
                            existing.get("name", "").strip().lower() == item_name.lower()
                            for existing in categories_map[matched_key]["items"]
                        )
                        if not item_exists:
                            categories_map[matched_key]["items"].append(item)
                else:
                    # Insert new category
                    categories_map[cat_name] = {
                        "name": cat_name,
                        "items": []
                    }
                    for item in cat.get("items", []):
                        item_name = item.get("name", "").strip()
                        if not item_name:
                            continue
                        categories_map[cat_name]["items"].append(item)

        avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 0.90

        # Build clean merged categories list
        merged_categories = list(categories_map.values())

        return {
            "success": True,
            "data": {
                "categories": merged_categories,
                "confidence": avg_confidence
            },
            "usage": {
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": round(total_cost, 6)
            }
        }
