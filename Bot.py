import asyncio
import httpx
import json
import os
from loguru import logger
from datetime import datetime
from panel import Panel, get_data_json
from dotenv import load_dotenv


load_dotenv()

API_TOKEN_TG = os.getenv("API_TOKEN_TG")
base_url = f"https://api.telegram.org/bot{API_TOKEN_TG}/"
path_sub = os.getenv("path_sub")

keyboard = {
    'keyboard': [
        [
            {"text": "Получить подписку"}
        ]
    ],
    'resize_keyboard': True,
    'is_persistent': True
}


class Bot:
    def __init__(self, panel: Panel):
        self.client = httpx.AsyncClient(base_url=base_url,timeout=35)
        self.panel = panel
        self.offset = 0


    async def get_updates(self) -> dict:
        """
        Запрашивает новые события и команды из Telegram API
        Обновляет локальную базу зарегистрированных пользователей
        Returns:
            dict: словарь пользователей в формате {chat_id: username}
        """
        params = {'offset': self.offset, 'timeout': 30}
        response = await self.client.get("getUpdates", params=params)
        response.raise_for_status()
        response = response.json()
        messages = response.get('result', [])

        if not messages:
            logger.debug("Не найдено новых сообщений!")

        current_users = {}

        if os.path.exists('data/users.json') and os.path.getsize('data/users.json') > 0:
            with open('data/users.json', 'r', encoding='UTF-8') as f:
                current_users = json.load(f)

        for item in messages:
            number_message = item['update_id']
            if 'message' not in item:
                self.offset = number_message + 1
                continue

            text = item['message'].get('text', '[Не текст]')
            chat_id = str(item['message']['chat']['id'])
            username = item['message']['from'].get('username', f"user_{chat_id}")

            logger.info(f"Мне пришло новое сообщение №{number_message} от {username}: {text}, в {datetime.now()}")

            if text == '/start':
                if chat_id not in current_users:
                    if await self.panel.add_client(username, await self.panel.get_id()) != -1:
                        logger.info(f"Пользователь {chat_id}:{username} добавлен!")
                        logger.info(f"Добавлены все протоколы у {chat_id}: {username}")

                        sub_id = await self.panel.get_sub_id()
                        sub_id = sub_id.get(username)
                        sub_user = path_sub + sub_id

                        current_users[chat_id] = {"username": username, "sub": sub_user}

                        with open('data/users.json', 'w', encoding='UTF-8') as f:
                            json.dump(current_users, f, indent=4)

                        response = await self.client.post("sendMessage", json={'chat_id': chat_id, 'text': sub_user, 'reply_markup': keyboard})
                        response.raise_for_status()
                else:
                    logger.warning(f"Пользователь {chat_id}:{username} уже существует!")
                    sub_user = current_users[chat_id]["sub"]
                    response = await self.client.post("sendMessage", json={'chat_id': chat_id, 'text': sub_user, 'reply_markup': keyboard})
                    response.raise_for_status()
            elif text == "Получить подписку":
                if chat_id in current_users:
                    sub_user = current_users[chat_id]["sub"]
                    response = await self.client.post("sendMessage", json={'chat_id':chat_id, 'text': sub_user, 'reply_markup': keyboard})
                    response.raise_for_status()
            self.offset = number_message + 1

        return current_users


    async def send_message(self, text: str) -> bool:
        """
        Выполняет рассылку пользователям зарегистрированным пользователям в Telegram
        Args:
            text: сообщение, которое нужно отправить
        Returns:
            bool: возвращает True, если сообщения были отправлены, иначе False
        """
        if not os.path.exists('data/users.json') or os.path.getsize('data/users.json') == 0:
            logger.error("Файл users.json пуст или не существует.")
            return False

        dict_users = get_data_json('data/users.json')

        tasks = []

        for chat_id, user_data in dict_users.items():
            params = {'chat_id': chat_id, 'text': f"{user_data['username']}, {text}"}
            task = asyncio.create_task(self.client.post("sendMessage", json=params))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_sent = True
        for res in results:
            if isinstance(res, httpx.RequestError):
                all_sent = False
                logger.error(f"Сетевая ошибка: {res}")
            elif isinstance(res, Exception):
                all_sent = False
                logger.error(f"Ошибка при отправке: {res}")
            elif res.is_error:
                all_sent = False
                (logger.error
                 (f"Telegram вернул: {res.status_code}\n{res.text[:200]}"))
        return all_sent
