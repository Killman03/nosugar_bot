import json
import httpx
import asyncio
from typing import Optional
from loguru import logger

from config import settings


class RecipeService:
    """Service for generating sugar-free recipes using DeepSeek API."""
    
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.api_url = settings.deepseek_api_url
    
    async def generate_recipe(self, ingredients: str) -> Optional[str]:
        """Generate a sugar-free recipe based on provided ingredients."""
        try:
            prompt = f"""
            Создай рецепт блюда без сахара, используя следующие ингредиенты: {ingredients}
            
            Требования:
            - Блюдо должно быть вкусным и полезным
            - Не использовать сахар, мед, сиропы и другие подсластители
            - Можно использовать натуральные специи и травы
            - Укажи пошаговую инструкцию приготовления
            - Добавь примерное время приготовления
            
            Формат ответа:
            Название блюда
            
            Ингредиенты:
            - список ингредиентов
            
            Время приготовления: X минут
            
            Инструкция:
            1. Шаг 1
            2. Шаг 2
            и т.д.
            """
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    response = await asyncio.wait_for(
                        client.post(
                            self.api_url,
                            headers={
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": "deepseek-chat",
                                "messages": [
                                    {
                                        "role": "user",
                                        "content": prompt
                                    }
                                ],
                                "max_tokens": 1000,
                                "temperature": 0.7
                            }
                        ),
                        timeout=30.0  # 30 seconds timeout
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        recipe_text = data["choices"][0]["message"]["content"]
                        logger.info(f"Generated recipe for ingredients: {ingredients}")
                        return recipe_text
                    else:
                        logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                        return None
                        
                except asyncio.TimeoutError:
                    logger.warning(f"DeepSeek API request timeout for ingredients: {ingredients}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error generating recipe: {e}")
            return None
    
    async def get_alternative_snacks(self) -> str:
        """Get alternative snack suggestions when user wants sweets."""
        try:
            # Simulate AI processing time
            await asyncio.sleep(2)
            
            alternatives = [
                "🍎 Яблоко с корицей",
                "🥜 Горсть орехов (миндаль, грецкие орехи)",
                "🥑 Авокадо с солью и перцем",
                "🥕 Морковные палочки с хумусом",
                "🍓 Клубника или другие ягоды",
                "🥚 Вареное яйцо",
                "🧀 Кусочек сыра",
                "🥬 Листья салата с оливковым маслом",
                "🌰 Семечки подсолнуха или тыквы",
                "🥛 Греческий йогурт без добавок"
            ]
            
            return "Вместо сладкого попробуйте:\n\n" + "\n".join(alternatives)
            
        except Exception as e:
            logger.error(f"Error getting alternative snacks: {e}")
            return "Вместо сладкого попробуйте:\n\n🍎 Яблоко с корицей\n🥜 Горсть орехов\n🥑 Авокадо" 