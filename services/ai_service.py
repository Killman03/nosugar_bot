import asyncio
from dotenv import load_dotenv
import os
from typing import Optional
from openai import OpenAI
from loguru import logger


class AIService:
    """Service for AI-powered recipe generation using DeepSeek."""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        # Используем правильный URL для DeepSeek API
        self.base_url = "https://api.deepseek.com"

        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY not found in environment variables")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
    
    async def generate_recipe(self, ingredients: str) -> str:
        """Generate a healthy recipe without sugar using the provided ingredients."""
        if not self.client:
            return self._get_fallback_recipe(ingredients)
        
        try:
            system_prompt = """Ты - эксперт по здоровому питанию и кулинарии. Твоя задача - создавать вкусные и полезные рецепты без добавления сахара.

Правила:
1. НЕ добавляй сахар, сиропы или другие подсластители
2. Используй только натуральные ингредиенты или продукты из фруктозы
3. Рецепт должен быть простым и доступным
4. Укажи время приготовления
5. Добавь полезные советы по приготовлению
6. Рецепт должен быть на русском языке

Формат ответа:
🍳 [Название блюда]

⏰ Время приготовления: [X минут]

🥗 Ингредиенты:
- [список ингредиентов]

👨‍🍳 Приготовление:
1. [шаг 1]
2. [шаг 2]
...

💡 Полезный совет: [совет по приготовлению или пользе блюда]"""

            user_prompt = f"Создай рецепт здорового блюда без сахара, используя эти ингредиенты: {ingredients}"

            # Add timeout for AI request
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        stream=False,
                        temperature=0.7,
                        max_tokens=1000
                    ),
                    timeout=30.0  # 30 seconds timeout
                )
                
                recipe = response.choices[0].message.content
                logger.info(f"Generated recipe for ingredients: {ingredients}")
                return recipe
                
            except asyncio.TimeoutError:
                logger.warning(f"AI request timeout for ingredients: {ingredients}")
                return self._get_fallback_recipe(ingredients)
            
        except Exception as e:
            logger.error(f"Error generating recipe with DeepSeek: {e}")
            return self._get_fallback_recipe(ingredients)
    
    def _get_fallback_recipe(self, ingredients: str) -> str:
        """Fallback recipe when AI service is not available."""
        return f"""🍳 Здоровый салат

⏰ Время приготовления: 15 минут

🥗 Ингредиенты:
- {ingredients}
- Оливковое масло
- Лимонный сок
- Соль и перец по вкусу

👨‍🍳 Приготовление:
1. Нарежьте все ингредиенты
2. Смешайте в большой миске
3. Добавьте оливковое масло и лимонный сок
4. Посолите и поперчите по вкусу
5. Аккуратно перемешайте

💡 Полезный совет: Этот салат богат витаминами и клетчаткой, что поможет утолить голод без вреда для здоровья!"""
    
    async def generate_motivation(self, streak: int) -> str:
        """Generate motivational message using AI."""
        if not self.client:
            return self._get_fallback_motivation(streak)
        
        try:
            system_prompt = """Ты - мотивационный тренер, специализирующийся на здоровом образе жизни и отказе от сахара. 

Твоя задача - создавать вдохновляющие и поддерживающие сообщения, которые помогут людям продолжать их путь к здоровому питанию.

Правила:
1. Будь позитивным и поддерживающим
2. Упоминай конкретные достижения (серия дней)
3. Давай практические советы
4. Используй эмодзи для эмоциональности
5. Сообщение должно быть на русском языке
6. Длина: 2-3 предложения"""

            user_prompt = f"Создай мотивационное сообщение для человека, который уже {streak} дней не ест сахар"

            # Add timeout for AI request
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        stream=False,
                        temperature=0.8,
                        max_tokens=200
                    ),
                    timeout=15.0  # 15 seconds timeout for motivation
                )
                
                motivation = response.choices[0].message.content
                logger.info(f"Generated motivation for streak: {streak}")
                return motivation
                
            except asyncio.TimeoutError:
                logger.warning(f"AI request timeout for motivation with streak: {streak}")
                return self._get_fallback_motivation(streak)
            
        except Exception as e:
            logger.error(f"Error generating motivation with DeepSeek: {e}")
            return self._get_fallback_motivation(streak)
    
    def _get_fallback_motivation(self, streak: int) -> str:
        """Fallback motivation when AI service is not available."""
        if streak == 0:
            return "💪 Каждый день - это новая возможность начать здоровую жизнь! Ты можешь это сделать!"
        elif streak < 7:
            return f"🔥 Отличное начало! {streak} дней без сахара - это уже серьезный прогресс! Продолжай в том же духе!"
        elif streak < 30:
            return f"🌟 Невероятно! {streak} дней здорового питания! Ты формируешь полезные привычки!"
        else:
            return f"🏆 Потрясающе! {streak} дней без сахара! Ты настоящий герой здорового образа жизни!" 
    
    async def generate_weekly_challenge(self) -> str:
        """Generate weekly challenge using AI."""
        if not self.client:
            return self._get_fallback_weekly_challenge()
        
        try:
            system_prompt = """Ты - эксперт по здоровому образу жизни и мотивации. Твоя задача - создавать интересные и выполнимые недельные челленджи для людей, которые отказываются от сахара.

Правила для челленджей:
1. Челлендж должен быть выполнимым за неделю
2. Связан с отказом от сахара или здоровым образом жизни
3. Должен быть интересным и мотивирующим
4. Может включать физические упражнения, питание, привычки
5. Должен быть на русском языке
6. Длина: 1-2 предложения
7. Без использования сахара и подсластителей

Примеры хороших челленджей:
- "Пей только воду и несладкий чай всю неделю"
- "Делай 20 приседаний каждый день"
- "Гуляй 30 минут на свежем воздухе каждый день"
- "Ешь фрукты вместо сладостей всю неделю"
- "Делай дыхательные упражнения 5 минут утром"

Формат ответа:
🎯 [Название челленджа]

[Описание челленджа в 1-2 предложения]"""

            user_prompt = "Создай интересный недельный челлендж для человека, который отказывается от сахара"

            # Add timeout for AI request
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        stream=False,
                        temperature=0.8,
                        max_tokens=150
                    ),
                    timeout=15.0  # 15 seconds timeout for challenge
                )
                
                challenge = response.choices[0].message.content
                logger.info(f"Generated weekly challenge: {challenge}")
                return challenge
                
            except asyncio.TimeoutError:
                logger.warning("AI request timeout for weekly challenge")
                return self._get_fallback_weekly_challenge()
            
        except Exception as e:
            logger.error(f"Error generating weekly challenge with DeepSeek: {e}")
            return self._get_fallback_weekly_challenge()
    
    def _get_fallback_weekly_challenge(self) -> str:
        """Fallback weekly challenge when AI service is not available."""
        import random
        
        challenges = [
            "🎯 Неделя без сладких напитков\n\nПей только воду, несладкий чай и кофе всю неделю. Замени газировки и соки на полезные альтернативы!",
            "🎯 Ежедневные прогулки\n\nГуляй 30 минут на свежем воздухе каждый день. Это поможет укрепить здоровье и отвлечься от желания сладкого!",
            "🎯 Фруктовая неделя\n\nЕшь фрукты вместо сладостей всю неделю. Яблоки, груши, апельсины - натуральная сладость без вреда!",
            "🎯 Утренняя зарядка\n\nДелай 10 приседаний и 10 отжиманий каждое утро. Физическая активность поможет укрепить силу воли!",
            "🎯 Водная неделя\n\nВыпивай 2 литра воды каждый день. Вода поможет очистить организм и снизить тягу к сладкому!",
            "🎯 Медитация\n\nПрактикуй 5 минут медитации каждый день. Это поможет справиться со стрессом без сладкого!",
            "🎯 Здоровый завтрак\n\nГотовь полезный завтрак каждый день: овсянка, яйца, творог. Начни день правильно!"
        ]
        
        return random.choice(challenges) 