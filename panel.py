import asyncio
import time
import httpx
import json
import os
from loguru import logger
from dotenv import load_dotenv


load_dotenv()

API_TOKEN_PANEL = os.getenv("API_TOKEN_PANEL")
base_url = os.getenv("base_url")
headers = {"Authorization": f"Bearer {API_TOKEN_PANEL}"}


def get_data_json(file_name: str) -> dict | list:
    """
        Десериализует данные json (превращает JSON строку в python объект)
        Args:
            file_name: Названия файла в строквом виде (str)
        Returns: преобразованную JSON строку в список или словарь
         """
    with open(file_name, 'r', encoding='UTF-8') as file:
        data = json.load(file)
    return data


class Panel:
    def __init__(self,
                 base_url: str = base_url,
                 headers: dict | None = None
                 ) -> None:
        if headers is None:
            headers = {"Authorization": f"Bearer {API_TOKEN_PANEL}"}
        self.client = httpx.AsyncClient(base_url=base_url, headers=headers, timeout=10)


    async def get_keys(self) -> dict:
        """
            Формирует приватный и публичный ключи
            Returns:
                dict: Словарь с ключами 'privateKey' и 'publicKeY'
            """
        response = await self.client.get("server/getNewX25519Cert")
        response.raise_for_status()
        return response.json()['obj']


    async def get_id(self) -> list | None:
        """
            Возвращает все айди, существующих inbounds
            Returns:
                list | None: Список ID, либо None, если данные не найдены
            """
        response = await self.client.get("inbounds/options")
        response.raise_for_status()

        data = response.json().get('obj')

        if data is None:
            return None

        new_inbound_ids = [key['id'] for key in data]

        old_inbound_ids = []
        if os.path.exists('data/inbound_ids.json') and os.path.getsize('data/inbound_ids.json') > 0:
            old_inbound_ids = get_data_json('data/inbound_ids.json')

        if new_inbound_ids != old_inbound_ids:
            with open('data/inbound_ids.json', 'w', encoding='UTF-8') as f:
                json.dump(new_inbound_ids, f, indent=4)
            logger.info(f"Обнаружены изменения в inbounds! Файл inbound_ids.json обновлен")

        return new_inbound_ids




    async def get_status_options(self, list_inbound_ids: list | None) -> int:
        """
        Проверяет статус настроек inbounds на сервере 3x-ui и обновляет локальный файл
        Args:
            list_inbound_ids: список ID inbounds. Если None, берет из inbound_ids.json
        Returns:
            -1: Не найдены настройки (список ID inbounds пуст)
            0: Настройки не изменились
            1: Настройки изменились
            2: Создан локальный файл server_options.json
        """
        if list_inbound_ids is None:
            return - 1

        current_options = []
        tasks = []
        async with asyncio.TaskGroup() as tg:
            for item_id in list_inbound_ids:
                task = tg.create_task(self.client.get(f"inbounds/get/{item_id}"))
                tasks.append(task)

        for task in tasks:
            response = task.result()
            response.raise_for_status()
            content = response.json()

            if content['obj']['enable'] == True:
                inbound = content['obj']
                # print(item_id, content['obj']['tag'],content['obj']['enable'])
                inbound.pop("up", None)
                inbound.pop("down", None)
                inbound.pop("clientStats", None)
                inbound.pop('settings', None)

                current_options.append(inbound)

        if not os.path.exists('data/server_options.json') or os.path.getsize('data/server_options.json') == 0:
            with open('data/server_options.json', 'w', encoding='UTF-8') as f:
                json.dump(current_options, f, indent=4)
            return 2

        with open('data/server_options.json', 'r', encoding='UTF-8') as f:
            old_options = json.load(f)
            if old_options != current_options:
                with open('data/server_options.json', 'w', encoding='UTF-8') as f:
                    json.dump(current_options, f, indent=4)
                    return 1
            else:
                return 0


    async def add_client(self, telegram_username: str, list_inbound_ids: list) -> dict | int:
        """
        Добавляет на сервер клиента после регистрации (/start) в Telegram
        Args:
            telegram_username: имя пользователя в Telegram
            list_inbound_ids: список всех существующих ID inbounds для привязки
        Returns:
            dict | int: Возвращает словарь созданного пользователя, если список ID inbounds пуст, то -1
        """
        if not list_inbound_ids:
            return -1

        new_client = {
            'client': {
                'email': telegram_username,
                'totalGB': 0,
                'expiryTime': 0,
                'limitIp': 0,
                'enable': True
            },
            'inboundIds': list_inbound_ids
        }
        response = await self.client.post("clients/add", json=new_client)
        response.raise_for_status()
        return response.json()

    async def attach_inbound(self, telegram_username) -> None:
        """
        Добавляет пользователю все существующие inbounds
        Args:
            telegram_username: имя пользователя в Telegram
        """
        list_inbound_ids = get_data_json('data/inbound_ids.json')

        new_inbounds = {
            'inboundIds': list_inbound_ids
        }
        response = await self.client.post(f"clients/{telegram_username}/attach", json=new_inbounds)
        response.raise_for_status()

    async def get_sub_id(self):
        response = await self.client.get("inbounds/list")
        response.raise_for_status()
        response = response.json()["obj"][0]["clientStats"]
        result = {dt["email"]:dt["subId"] for dt in response}
        return result


async def main():
    panel = Panel()
    try:
        start = time.perf_counter()
        async with asyncio.TaskGroup() as tg:
            tasks = [
            tg.create_task(panel.get_keys()),
            tg.create_task(panel.get_keys()),
            tg.create_task(panel.get_keys())
            ]

        results = [task.result() for task in tasks]
        for res in results:
            print(res, time.perf_counter() - start)
        print(time.perf_counter() - start)
    finally:
        await panel.client.aclose()


if __name__ == "__main__":
    panel = Panel()
    print(asyncio.run(panel.get_sub_id()))
