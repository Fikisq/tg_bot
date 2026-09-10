import asyncio
import json
import httpx
from panel import Panel
from Bot import Bot
from loguru import logger


logger.add(
    'logs.log',
    level='DEBUG',
    rotation='10 MB',
    compression='zip'
)

async def telegram_loop(bot: Bot) -> None:
    """Бесконечный цикл обработки сообщений Telegram!"""
    while True:
        try:
            await bot.get_updates()
        except httpx.HTTPStatusError as error:
            logger.error(f"Telegram/Panel вернул статус: {error.response.status_code}, {error.response.text[:200]}")
            await asyncio.sleep(3)
        except httpx.RequestError as error:
            logger.error(f"Ошибка: {error}")
            await asyncio.sleep(3)
        except json.JSONDecodeError as error:
            logger.error(f"Получен некорректный JSON: {error}")
            await asyncio.sleep(3)
        except Exception as error:
            logger.error(f"Неожиданная ошибка в: {error}")
            raise


async def panel_pool(panel: Panel, bot: Bot) -> None:
    """Бесконечный цикл мониторинга изменений на сервере"""
    while True:
        try:
            list_inbound_ids = await panel.get_id()
            status_options = await panel.get_status_options(list_inbound_ids)
            if status_options == -1:
                logger.warning(f"Не найдены ID inbounds на сервере")
            elif status_options == 0:
                pass
            elif status_options == 1:
                logger.info("Настройки изменились! Отправить сообщение в телеграмм!")
                await bot.send_message("обновите подписку для корректной работы!")
            else:
                logger.info("Файл server_options.json был создан!")
        except* httpx.HTTPStatusError as error:
            logger.error(f"Ошибка: {error}")
        except* httpx.RequestError as error:
            logger.error(f"Ошибка: {error}")
        except* json.JSONDecodeError as error:
            logger.error(f"Панель вернула не json: {error}")
        except* Exception as error:
            logger.error(f"Неожиданная ошибка в: {error}")
            raise
        finally:
            await asyncio.sleep(10)


async def main() -> None:
    logger.info("Бот запущен!")
    panel = Panel()
    bot = Bot(panel)
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(telegram_loop(bot))
            tg.create_task(panel_pool(panel, bot))
    except KeyboardInterrupt as error:
        logger.info(f"Программа остановлена вручную")

    finally:
        await panel.client.aclose()
        await bot.client.aclose()



if __name__ == "__main__":
    asyncio.run(main())
