from fastapi import FastAPI, Response, WebSocket
from fastapi.responses import StreamingResponse
import asyncio
import uvicorn
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TextIteratorStreamer, GenerationConfig
from peft import PeftModel
import time
import csv
import asyncio
from threading import Thread
import logging
import requests
from queue import Empty
from fastapi.middleware.cors import CORSMiddleware

base_model_id = "mistralai/Mistral-7B-v0.1"
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id,  # Mistral, same as before
    quantization_config=bnb_config,  # Same quantization config as before
    device_map="auto",
    trust_remote_code=True,
    use_auth_token=True
)

tokenizer = AutoTokenizer.from_pretrained(base_model_id, add_bos_token=True, trust_remote_code=True)
streamer = TextIteratorStreamer(tokenizer)
model = PeftModel.from_pretrained(base_model, "/home/ainura/mistral/checkpoint-36000")
def formatting_func(example):
    text = f"<s>[KYR] {example} [/KYR] "
    return text
app = FastAPI()
origins = ["http://localhost", "http://localhost:8000", "http://127.0.0.1:9000", "http://127.0.0.1:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
async def consume_streamer(stream):
    while True:
        try:
            for token in stream:
                yield token
            break
        except Empty:
            # The streamer raises an Empty exception if the next token
            # hasn't been generated yet. `await` here to yield control
            # back to the event loop so other coroutines can run.
            await asyncio.sleep(0.001)
async def generate_response(text):
    print(text)
    with torch.no_grad():
        prompt = formatting_func(text)
        input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to('cuda')
        generate_args = {
            "max_new_tokens": 200,
            "eos_token_id": tokenizer.eos_token_id,
            "pad_token_id": tokenizer.pad_token_id,
        }
        generation_config = GenerationConfig(**generate_args)
        generation_kwargs = {
            "input_ids": input_ids,
            "generation_config": generation_config,
            "return_dict_in_generate": True,
            "output_scores": True,
            "max_new_tokens": 200,
            "streamer": streamer,
        }
        # Begin generation in a separate thread
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()
    async for i in consume_streamer(streamer):
        yield i

@app.get("/process_text/{message}")
async def process_text(message):
    print(message)
    # data = request.POST['message']
    return StreamingResponse(generate_response(message), media_type="application/json")

if __name__ == "__main__":

    uvicorn.run(app, host="127.0.0.1", port=8000)
