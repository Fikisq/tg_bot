import asyncio
import time
from asyncio import gather

import httpx

base_url = "https://petstore.swagger.io/v2/"
client= httpx.AsyncClient(base_url=base_url,timeout=5)

async def get_status():
    start = time.perf_counter()
    params = {"status": "available"}
    response = await client.get("pet/findByStatus", params=params)
    print(f"get_status: {response.status_code} за {time.perf_counter()-start}")

async def post_pet(petId: int):
    start = time.perf_counter()
    with open("screen.png", "rb") as image:
        response = await client.post(f"pet/{petId}/uploadImage", data={"additionalMetadata": "test image"}, files={"file":image})
    print(f"post_pet: {response.status_code} за {time.perf_counter()-start}")

async def main():
    results = await asyncio.gather(post_pet(1),get_status())
if __name__ == "__main__":
    asyncio.run(main())