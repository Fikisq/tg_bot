import asyncio
from contextvars import ContextVar, copy_context, Context
import time
from itertools import count

# ctx_num = ContextVar('global_num')
# ctx_num.set(12)
# ctx = copy_context()
# print(ctx_num)
#
# async def coro():
#     local_start = time.perf_counter()
#     print("Засыпаю на одну секунду")
#     await asyncio.sleep(1)
#     print(f"Снова работаю!  Прошло {time.perf_counter() - local_start}")
#     return inner_coro()
#
# def inner_coro():
#     return ctx_num.get()


# async def main():
#     pass

# def my_callback(task: asyncio.Task):
#     print(f"Вызван my_callback! Имя задачи {task.get_name()}, результат: {task.result()}")
#
#
# if __name__ == "__main__":
#     start = time.perf_counter()
#     print("Запускаю главную корутину")
#     asyncio.run(main())


lst =[1,2,3]
print(lst.pop())