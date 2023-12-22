from threading import Thread

import torch
from peft import PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    GenerationConfig,
    TextIteratorStreamer,
    BitsAndBytesConfig,
)

DEFAULT_MAX_LENGTH = 4096

base_model_id = "mistralai/Mistral-7B-v0.1"
class Model:
    def __init__(self, **kwargs):
        self.tokenizer = None
        self.model = None

    def load(self):
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            base_model_id,  # Mistral, same as before
            quantization_config=bnb_config,  # Same quantization config as before
            device_map="auto",
            trust_remote_code=True,
            use_auth_token=True
        )
        self.model = PeftModel.from_pretrained(self.model, "/home/ainura/mistral/checkpoint-15000", stream=True)

        self.tokenizer = AutoTokenizer.from_pretrained(
            "mistralai/Mistral-7B-v0.1",
            device_map="auto",
            torch_dtype=torch.float16,
            stream=True
        )

    def preprocess(self, request: dict):
        generate_args = {
            "max_new_tokens": 128,
            "temperature": 1.0,
            "top_p": 0.95,
            "top_k": 50,
            "repetition_penalty": 1.0,
            "no_repeat_ngram_size": 0,
            "use_cache": True,
            "do_sample": True,
            "eos_token_id": self.tokenizer.eos_token_id,
            "pad_token_id": self.tokenizer.pad_token_id,
        }
        if "max_tokens" in request.keys():
            generate_args["max_new_tokens"] = request["max_tokens"]
        if "temperature" in request.keys():
            generate_args["temperature"] = request["temperature"]
        if "top_p" in request.keys():
            generate_args["top_p"] = request["top_p"]
        if "top_k" in request.keys():
            generate_args["top_k"] = request["top_k"]
        request["generate_args"] = generate_args
        return request

    def stream(self, input_ids: list, generation_args: dict):
        streamer = TextIteratorStreamer(self.tokenizer)
        generation_config = GenerationConfig(**generation_args)
        generation_kwargs = {
            "input_ids": input_ids,
            "generation_config": generation_config,
            "return_dict_in_generate": True,
            "output_scores": True,
            "max_new_tokens": generation_args["max_new_tokens"],
            "streamer": streamer,
        }

        with torch.no_grad():
            # Begin generation in a separate thread
            thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
            thread.start()

            # Yield generated text as it becomes available
            def inner():
                for text in streamer:
                    yield text
                thread.join()

        return inner()

    def predict(self, request: dict):
        stream = request.pop("stream", False)
        prompt = request.pop("prompt")
        generation_args = request.pop("generate_args")
        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids.cuda()

        if stream:
            return self.stream(input_ids, generation_args)

        with torch.no_grad():
            try:
                output = self.model.generate(inputs=input_ids, **generation_args)
                return self.tokenizer.decode(output[0])
            except Exception as exc:
                return {"status": "error", "data": None, "message": str(exc)}


model = Model()
model.load()

inputs = model.tokenizer(["Жашоонун мааниси кандай?"], return_tensors="pt").to('cuda')

streamer = TextIteratorStreamer(model.tokenizer)
generation_kwargs = dict(inputs, streamer=streamer, max_new_tokens=300)

thread = Thread(target=model.model.generate, kwargs=generation_kwargs)

thread.start()

generated_text = ""

for new_text in streamer:
    generated_text += new_text

print(generated_text)

