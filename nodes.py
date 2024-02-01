import os
from PIL import Image
import torch
import numpy as np
import comfy.utils
import comfy.model_management

from .moondream import Moondream
from transformers import (
    TextIteratorStreamer,
    CodeGenTokenizerFast as Tokenizer,
)

script_directory = os.path.dirname(os.path.abspath(__file__))

class MoondreamQuery:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {  
            "images": ("IMAGE", ),
            "question": ("STRING", {"multiline": True, "default": "What is this?",}),
            },
            }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES =("text",)
    FUNCTION = "process"

    CATEGORY = "Moondream"

    def process(self, images, question):
        batch_size = images.shape[0]
        device = comfy.model_management.get_torch_device()
        dtype = torch.float16 if comfy.model_management.should_use_fp16() and not comfy.model_management.is_device_mps(device) else torch.float32
        
        checkpoint_path = os.path.join(script_directory, f"checkpoints/moondream1")

        if os.path.exists(checkpoint_path):
                checkpoint_path = checkpoint_path
        else:
            try:
                from huggingface_hub import snapshot_download
                snapshot_download(repo_id=f"vikhyatk/moondream1", ignore_patterns=["*.pt","*.bin"],local_dir=checkpoint_path, local_dir_use_symlinks=False)
            except:
                raise FileNotFoundError("No model found.")
       
        tokenizer = Tokenizer.from_pretrained(checkpoint_path)
        moondream = Moondream.from_pretrained(checkpoint_path).to(device=device, dtype=dtype)
        moondream.eval()

        answer_dict = {}
        if batch_size > 1:
            for i in range(batch_size):
                image = Image.fromarray(np.clip(255. * images[i].cpu().numpy(),0,255).astype(np.uint8))
                image_embeds = moondream.encode_image(image)
                answer = moondream.answer_question(image_embeds, question, tokenizer)
                answer_dict[str(i)] = answer

            formatted_answers = ",\n".join([f'"{frame}" : "{answer}"' for frame, answer in answer_dict.items()])
            formatted_output = "{\n" + formatted_answers + "\n}"
            print(formatted_output)
            return formatted_output,
        else:
            image = Image.fromarray(np.clip(255. * images[0].cpu().numpy(),0,255).astype(np.uint8))
            image_embeds = moondream.encode_image(image)
            answer = moondream.answer_question(image_embeds, question, tokenizer)
            return answer,
        


NODE_CLASS_MAPPINGS = {
    "MoondreamQuery": MoondreamQuery,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "MoondreamQuery": "MoondreamQuery",
}