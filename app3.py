import httpx
import asyncio

async def make_request():
    async with httpx.AsyncClient() as client:
        text = 'Салам кандай'
        response = await client.get(f"http://127.0.0.1:8000/process_text/{text}")
        print(response)
        async for chunk in response.aiter_text():
            for char in chunk:
                print(char, end='', flush=True)

    #print(response.text)

if __name__ == "__main__":

    asyncio.run(make_request())
