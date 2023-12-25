from fastapi import FastAPI, Response, WebSocket
from fastapi.responses import StreamingResponse
import asyncio
import uvicorn

app = FastAPI()

async def generate_response(text):
    print(text)
    promt = 'sdjf dfsgiu ugiuf sgiusgua udgfuisd iidsgius fgsduigusd gfduh hgfduhguhdfgod uidfsgudfug ggsh gfdsfgds hods'
    for char in promt:
        yield char
        await asyncio.sleep(0.1)  # Имитация обработки буквы, замените на реальную логику

@app.get("/process_text/{text}")
async def process_text(text: str):
    return StreamingResponse(generate_response(text), media_type="text/plain")

if __name__ == "__main__":

    uvicorn.run(app, host="127.0.0.1", port=8000)
