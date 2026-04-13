import torch
import re
from PIL import Image
from transformers import pipeline, GenerationConfig

MODEL_ID = "google/gemma-4-E2B-it" # "google/gemma-4-E2B-it","google/gemma-4-E4B-it", "google/gemma-4-31B-it", "google/gemma-4-26B-A4B-it"

class VisionAnalyzer:
    def __init__(self):
        self.vqa_pipe = None
        if not torch.cuda.is_available():
            print("CUDA is NOT available. It could take a long time.")
        
    def analyze(self, target_img,desc):
        if desc is None:
            return None
        if self.vqa_pipe is None:
            try:
                self.vqa_pipe = pipeline(
                    task="image-text-to-text",
                    model=MODEL_ID,
                    device_map="auto",
                    dtype="auto"
                )
            except Exception as e:
                print(f"Error load model {MODEL_ID}")
                print(e)
                sys.exit(1)

        config = GenerationConfig.from_pretrained(MODEL_ID)
        config.max_new_tokens = 512
        gen_kwargs = dict(generation_config=config)
                
        input_image = Image.open(target_img)
        #w, h = input_image.size
        #input_image.thumbnail((w // 4, h // 4))
        
        question = "Cherche " + desc + ". Est ce que tu vois ca sur l'image ? Réponds par une probabilité entre 0.0 et 1.0"
        messages = [
            {
                "role": "user", "content": [
                    {"type": "image", "image": input_image},
                    {"type": "text", "text": question}
                ]
            }
        ]
        
        output = self.vqa_pipe(messages, return_full_text=False, generate_kwargs=gen_kwargs)
        
        text = output[0]["generated_text"]
        match = re.search(r"-?\d+(\.\d+)?", text)
        value = float(match.group()) if match else None
        return value
