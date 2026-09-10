# import contextvars
# import asyncio
#
# ctx_name = contextvars.ContextVar("name", default=None)
#
# async def coro(user_name):
#     await asyncio.sleep(1)
#     ctx_name.set(user_name)
#     print(ctx_name.name, ctx_name.get())
#
#
# async def main():
#     async with asyncio.TaskGroup() as tg:
#         tg.create_task(coro("User_1"))
#         tg.create_task(coro("User_2"))
#
# if __name__ == "__main__":
#     asyncio.run(main())

import asyncio
import contextvars

int_ctx = contextvars.ContextVar("int_ctx", default=0)
int_global = 0

async def sub_coroutine():
    await asyncio.sleep(1)
    print(f'Число в контексте суб корутины: {int_ctx.get()}')
    print(f'Глобальное число в суб корутине: {int_global}')


async def main_coroutine(req_id):
    global int_global
    int_ctx.set(req_id)
    int_global = req_id
    await sub_coroutine()
    print(f'Число в контексте главной корутины: {int_ctx.get()}')
    print()


async def main():
    tasks = []
    for req_id in range(1, 4):
        tasks.append(asyncio.create_task(main_coroutine(req_id)))
    for task in tasks:
        await task

if __name__ == "__main__":
    asyncio.run(main())
