# import asyncio
# import contextvars
# from functools import partial
# import time
# from asyncio import TaskGroup
#
# async def coro_1():
#     await asyncio.sleep(1)
#     print("Выполнилась coro_1")
#     return 1
#
#
# async def coro_2():
#     await asyncio.sleep(2)
#     raise ValueError("Ошибка")
#     print("Выполнилась coro_2")
#     return 2
#
#
# async def coro_3():
#     await asyncio.sleep(3)
#     print("Выполнилась coro_3")
#     return 3
#
#
# async def coro_4():
#     await asyncio.sleep(4)
#     raise ValueError("Ошибка!")
#     print("Выполнилась coro_4")
#     return 4
#
#
#
# def my_callback(result: list, task: asyncio.Task):
#     if not task.cancelled():
#         error = task.exception()
#         if error:
#             result.append(error)
#         else:
#             result.append(task.result())
#     else:
#         result.append(f"Задача {task.get_name()} отменена!")
#     print(result)
#
# async def main():
#     result = []
#     ctx_result = partial(my_callback, result)
#     try:
#         async with asyncio.TaskGroup() as tg:
#             tg.create_task(coro_1()).add_done_callback(ctx_result)
#             tg.create_task(coro_2()).add_done_callback(ctx_result)
#             tg.create_task(coro_3()).add_done_callback(ctx_result)
#             tg.create_task(coro_4()).add_done_callback(ctx_result)
#     except Exception as error:
#         print(f"Игнорирую {repr(error)}")
#
#
# if __name__ == '__main__':
#     start_time = time.perf_counter()
#     asyncio.run(main())
#     print(f"\nAll done in {time.perf_counter() - start_time:.2f}")


import asyncio
import contextvars
from functools import partial


results = []
cancelled = []

async def callback(results: list, cancelled: list, task: asyncio.Task):
    if not task.cancelled():
        error = task.exception()
        if error:
            cancelled.append(error)
        else:
            results.append(task.result())


async def main():
    global results
    global cancelled

    ctx_result = partial(callback, results, cancelled)
    async with asyncio.TaskGroup() as tg:
        for coroutine in coroutines:
            tg.create_task(coroutine()).add_done_callback(ctx_result)


if __name__ == '__main__':
    asyncio.run(main())
