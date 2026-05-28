from app.services.pipeline import pipeline_function,model_gguf_q4,pth_path,PTH_FILENAME,GGUF_Q4_NAME,model_dir,REPO_ID
from huggingface_hub import login, hf_hub_download, snapshot_download
from dotenv import load_dotenv
import os
import subprocess
import torch
from llama_cpp import Llama
import random

load_dotenv()

hugging_face_token = os.getenv('hugging_face_token')
login(token=hugging_face_token)

if model_gguf_q4.exists() and pth_path.exists():
    print("model exists")
else:
    try:
        print("downloading models")
        if not pth_path.exists():
            print(f"Downloading fine-tuned {PTH_FILENAME} .pth weights...")
            hf_hub_download(
                repo_id=REPO_ID,
                filename=PTH_FILENAME,
                local_dir=str(model_dir),
                local_dir_use_symlinks=False,
            )
        
        if not model_gguf_q4.exists():
            print(f"Downloading fine-tuned {GGUF_Q4_NAME} .pth weights...")
            hf_hub_download(
                repo_id=REPO_ID,
                filename=GGUF_Q4_NAME,
                local_dir=str(model_dir),
                local_dir_use_symlinks=False,
            )
            
    except Exception as e:
        pipeline_function()
        print(f"Exception {e} running pipeline")
    

from transformers import AutoTokenizer
from torch import nn

#load_model
def load_llama():
    model = Llama(model_path = f"./app/utils/{GGUF_Q4_NAME}",
                  chat_format='llama',
                  embedding = True,
                  n_ctx=512,
                  n_threads=8
                  )
    return model

#classifer model
class CodeClassifier(nn.Module):

    def __init__(self, input_size=4096):
        super().__init__()

        self.classifier = nn.Linear(input_size, 1)

    def forward(self, x):

        return torch.sigmoid(self.classifier(x))
    
#embedding
def get_embedding(llm, text):

    embedding = llm.create_embedding(text)

    vector = embedding["data"][0]["embedding"]

    tensor_vec = torch.tensor(vector)
    
    if tensor_vec.dim() == 2:
        tensor_vec = tensor_vec.mean(dim=0)
        
    return tensor_vec.unsqueeze(0)

#load_classifier
def load_classifier():

    model = CodeClassifier()

    state_dict = torch.load(f'./app/utils/{PTH_FILENAME}', map_location="cpu")

    if "state_dict" in state_dict:
        state_dict = state_dict["state_dict"]

    model.load_state_dict(state_dict, strict=False)

    model.eval()

    return model

#inferencing
def predict(llm, classifier, text):

    print("Creating embedding...")

    embedding = get_embedding(llm, text)

    with torch.no_grad():

        score = classifier(embedding)

    return f'{score.item():.4f}'    

llm = load_llama()

classifier = load_classifier()

def code_quality(text):
    # Extract code_data dictionary if text is the wrapper response
    if isinstance(text, dict) and "code_data" in text:
        text = text["code_data"]

    code_snippets = []

    #clean_data fails and returns dict(andriod dev)
    if isinstance(text, dict):
        for key, value in text.items():
            if not isinstance(value, list):
                value = [value]
                
            for file_item in value:
                content = ""
                if isinstance(file_item, dict):
                    content = file_item.get("content") or file_item.get("text") or ""
                elif isinstance(file_item, str):
                    content = file_item
                
                if content.strip():
                    code_snippets.append(content)

    elif isinstance(text, list):
        for file_item in text:
            content = ""
            if isinstance(file_item, dict):
                content = file_item.get("content") or file_item.get("text") or ""
            elif isinstance(file_item, str):
                content = file_item
            
            if content.strip():
                code_snippets.append(content)
    
    #remove this for testing repos with non pinned projects or andriod dev projects
    if not code_snippets:
        return 0, "Intern"
   
    samples = random.sample(code_snippets, min(len(code_snippets), 10))

    code = []

    for item in samples:
        cleaned = " ".join(item.split()[:500])
        code.append(cleaned)

    scores = [float(predict(llm, classifier, snippet)) for snippet in code]
    
    score = sum(scores) / len(scores)
    
    if score < 0.3:
        return score*100,"Intern"
    elif score < 0.5:
        return score*100, "Fresher"
    elif score < 0.7:
        return score*100, "Mid"
    else:
        return score*100, "senior"