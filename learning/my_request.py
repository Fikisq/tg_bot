from datetime import datetime
import os.path
import secrets
import requests
import json
import uuid
import time
from loguru import logger

#API_TOKEN_PANEL =
#headers =
#API_TOKEN_TG =

file_server_options = '../data/server_options.json'  # хранит все настройки протоколов
file_inbound_ids = '../data/inbound_ids.json'  # хранит айди протоколов

logger.add(
    '../logs.log',
    level='INFO',
    rotation='10 MB',
    compression='zip',
    encoding="utf-8",
    enqueue=True
)


def get_keys() -> dict:
    """
    Формирует приватный и публичный ключи

    Returns:
        dict: Словарь с ключами 'privateKey' и 'publickKeY'
    """
    url = "https://russianserver.duckdns.org:60256/main/panel/api/server/getNewX25519Cert"
    response = requests.get(url=url, headers=headers, timeout=2 )
    response.raise_for_status()
    return response.json()['obj']


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


def get_id() -> list | None:
    """
    Возвращает все айди, существующих inbounds

    Returns:
        list | None: Список ID, либо None, если данные не найдены
    """
    url = "https://russianserver.duckdns.org:60256/main/panel/api/inbounds/options"
    response = requests.get(url=url,headers=headers,timeout=2)
    response.raise_for_status()
    data = response.json().get('obj')

    if data is None:
        logger.info('id протоколов не найдены!')
        return None

    new_inbound_ids = [key['id'] for key in data]

    old_inbound_ids = []
    if os.path.exists('../data/inbound_ids.json') and os.path.getsize('../data/inbound_ids.json') > 0:
        old_inbound_ids = get_data_json('../data/inbound_ids.json')

    if new_inbound_ids != old_inbound_ids:
        with open('../data/inbound_ids.json', 'w', encoding='UTF-8') as f:
            json.dump(new_inbound_ids, f, indent=4)
        logger.info(f"Обнаружены изменения в inbounds! Файл inbound_ids.json обновлен")

    return new_inbound_ids


def get_status_options(list_inbound_ids: list | None) -> int:
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
    for item_id in list_inbound_ids:
        current_url = f"https://russianserver.duckdns.org:60256/main/panel/api/inbounds/get/{item_id}"
        response = requests.get(url=current_url,headers=headers)
        response.raise_for_status()
        content = response.json()

        if content['obj']['enable'] == True:
            inbound = content['obj']
        #     print(item_id, content['obj']['tag'],content['obj']['enable'])
            inbound.pop("up", None)
            inbound.pop("down", None)
            inbound.pop("clientStats", None)
            inbound.pop('settings', None)

            current_options.append(inbound)

    if not os.path.exists('../data/server_options.json') or os.path.getsize('../data/server_options.json') == 0:
        with open('../data/server_options.json', 'w', encoding='UTF-8') as f:
            json.dump(current_options, f, indent=4)
        return 2

    with open('../data/server_options.json', 'r', encoding='UTF-8') as f:
        old_options = json.load(f)
        if old_options != current_options:
            with open('../data/server_options.json', 'w', encoding='UTF-8') as f:
                json.dump(current_options, f, indent=4)
                return 1
        else:
            return 0


def add_client(telegram_username: str, list_inbound_ids: list ) -> dict | int:
    """
    Добавляет на сервер клиента после регистрации (/start) в Telegram
    Args:
        telegram_username: user name пользователя в Telegram
        list_inbound_ids: список всех существующих ID inbounds для привязки

    Returns:
        dict | int: Возвращает словарь созданного пользователя, если список ID inbounds пуст, то -1
    """
    if list_inbound_ids is None:
        return -1
    url = "https://russianserver.duckdns.org:60256/main/panel/api/clients/add"
    new_client = {
        'client':{
            'email': telegram_username,
            'totalGB': 0,
            'expiryTime': 0,
            'limitIp': 0,
            'enable': True
        },
        'inboundIds':list_inbound_ids
    }
    response = requests.post(url=url, headers=headers, json=new_client,timeout=2)
    response.raise_for_status()
    return response.json()


def attach_inbound(chat_id: str) -> None:
    """
    Добавляет пользователю все существующие inbounds
    Args:
        chat_id: уникальный ID чата с пользователем в Telegram
    """
    list_inbound_ids = get_data_json('../data/inbound_ids.json')
    user = get_data_json('../data/users.json').get(chat_id)
    url = f"https://russianserver.duckdns.org:60256/main/panel/api/clients/{user}/attach"
    new_inbounds = {
        'inboundIds': list_inbound_ids
    }
    response = requests.post(url=url, headers=headers, json=new_inbounds,timeout=2)
    response.raise_for_status()


offset = 0


def get_updates() -> dict:
    """
    Запрашивает новые события и команды из Telegram API
    Обновляет локальную базу зарегистрированных пользователей
    Returns:
        dict: словарь пользователей в формате {chat_id: username}
    """
    url = f"https://api.telegram.org/bot{API_TOKEN_TG}/getUpdates"
    global offset
    params = {'offset': offset, 'timeout': 1}
    response = requests.get(url=url, params=params,timeout=2)
    response.raise_for_status()
    response = response.json()
    messages = response.get('result', [])

    if not messages:
        logger.debug("Не найдено новых сообщений!")

    current_users = {}

    if os.path.exists('../data/users.json') and os.path.getsize('../data/users.json') > 0:
        with open('../data/users.json', 'r', encoding='UTF-8') as f:
            current_users = json.load(f)

    is_updated = False
    for item in messages:
        number_message = item['update_id']

        if 'message' not    in item:
            offset = number_message + 1
            continue

        text = item['message'].get('text', '[Не текст]')
        chat_id = str(item['message']['chat']['id'])
        username = item['message']['from'].get('username', f"user_{chat_id}")

        if text == '/start':
            if chat_id not in current_users:
                current_users[chat_id] = username
                if add_client(username, get_id()) != -1:
                    is_updated = True
                    logger.info(f"Пользователь {chat_id}:{username} добавлен!")
            else:
                logger.warning(f"Пользователь {chat_id}:{username} уже существует!")

        if text == '/new_inbounds':
            attach_inbound(chat_id)
            logger.info(f"Добавлены все протоколы у {chat_id}: {username}")

        logger.info(f"Мне пришло новое сообщение №{number_message} от {username}: {text}, в {datetime.now()}")
        offset = number_message + 1

    if is_updated:
        with open('../data/users.json', 'w', encoding='UTF-8') as f:
            json.dump(current_users, f, indent=4)
    return current_users


def send_message(dict_current_users) -> bool:
    """
    Выполняет рассылку пользователям зарегистрированным пользователям в Telegram
    Args:
        dict_current_users: словарь пользователей в формате {chat_id: username}
    Returns:
        bool : возвращает True, если сообщения были отправлены, иначе False
    """
    url = f"https://api.telegram.org/bot{API_TOKEN_TG}/sendMessage"

    if not os.path.exists('../data/users.json') or os.path.getsize('../data/users.json') == 0:
        logger.warning("Файл users.json пуст или не существует. Рассылка отменена")
        return False

    dict_users = get_data_json('../data/users.json')

    for chat_id, username in dict_current_users.items():
        params ={'chat_id':chat_id,'text':"Обновите подписку для корректной работы!"}
        response = requests.post(url=url,json=params,timeout=2)
        response.raise_for_status()
    return True


logger.info('Бот запущен и готов к работе')
last_check_time = time.time()
while True:
    try:
        dict_current_users = get_updates()
        current_time = time.time()
        if current_time - last_check_time >= 10:
            logger.debug("Прошло 10 секунд")
            list_inbound_ids = get_id()

            status_options = get_status_options(list_inbound_ids)
            if status_options == -1:
                logger.warning(f"Не найдены ID inbounds на сервере")
                break
            elif status_options == 0:
                logger.debug("Настройка не изменились!")
            elif status_options == 1:
                logger.info("Настройки изменились! Отправить сообщение в телеграмм!")
                send_message(dict_current_users)
            else:
                logger.info("Файл server_options.json был создан!")
            last_check_time = current_time
        time.sleep(2)


    except requests.exceptions.SSLError as e:
        logger.error(f"Сбой шифрования: {e}")
    except requests.exceptions.ConnectTimeout as e:
        logger.error(f'Превышено время ожидания')
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Сеть недоступна: {e}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Ошибка HTTP: {e}")
    except KeyboardInterrupt as e:
        logger.debug("Бот остановлен вручную")
        break
    except Exception as e:
        logger.error(f"Непредвиденная ошибка в логике: {e}")