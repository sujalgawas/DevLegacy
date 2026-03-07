from transformers import AutoModel,AutoTokenizer

from huggingface_hub import login, hf_hub_download

from dotenv import load_dotenv
import os


load_dotenv()

hugging_face_token = os.getenv('hugging_face_token')  
print(hugging_face_token)
login(token = hugging_face_token)

model_path = './backend/app/utils/Codellama_v2.pth'
repo_id = "sujalgawas/my-codellama-experience-model"
local_dir = "./backend/app/utils"
file_name = "Codellama_v2.pth"

if not os.path.exists(model_path):
    hf_hub_download(repo_id=repo_id,
                      local_dir=local_dir,
                      filename=file_name,
                      local_dir_use_symlinks=False)

