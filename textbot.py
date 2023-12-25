import asyncio
import logging
from queue import Empty
import torch
from fastapi import FastAPI
from starlette.responses import StreamingResponse
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer, BitsAndBytesConfig
from peft import PeftModel
from ray import serve

def formatting_func(example):
    text = f"<s>[KYR] {example} [/KYR] "
    return text

logger = logging.getLogger("ray.serve")
fastapi_app = FastAPI()
base_model_id = "mistralai/Mistral-7B-v0.1"


@serve.deployment
@serve.ingress(fastapi_app)
class Textbot:
    def __init__(self, model_id: str):
        self.loop = asyncio.get_running_loop()

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        self.model_id = model_id
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,  # Mistral, same as before
            quantization_config=bnb_config,  # Same quantization config as before
            device_map="auto",
            trust_remote_code=True,
            use_auth_token=True
        )
        self.tokenizer = AutoTokenizer.from_pretrained(base_model_id, add_bos_token=True, trust_remote_code=True)
        self.ft_model = PeftModel.from_pretrained(self.model, "/home/ainura/mistral/checkpoint-12000")

    @fastapi_app.post("/")
    def handle_request(self, prompt: str) -> StreamingResponse:
        logger.info(f'Got prompt: "{prompt}"')
        streamer = TextIteratorStreamer(
            self.tokenizer, timeout=0, skip_prompt=True, skip_special_tokens=True
        )
        self.loop.run_in_executor(None, self.generate_text, prompt, streamer)
        return StreamingResponse(
            self.consume_streamer(streamer), media_type="text/plain"
        )

    def generate_text(self, prompt: str, streamer: TextIteratorStreamer):
        #input_ids = self.tokenizer([prompt], return_tensors="pt").input_ids
        input_ids = self.tokenizer([prompt], return_tensors="pt").to("cuda")
        self.ft_model.generate(input_ids, streamer=streamer, max_length=100)

    async def consume_streamer(self, streamer: TextIteratorStreamer):
        while True:
            try:
                for token in streamer:
                    logger.info(f'Yielding token: "{token}"')
                    yield token
                break
            except Empty:
                # The streamer raises an Empty exception if the next token
                # hasn't been generated yet. `await` here to yield control
                # back to the event loop so other coroutines can run.
                await asyncio.sleep(0.001)

app = Textbot.bind("mistralai/Mistral-7B-v0.1")



