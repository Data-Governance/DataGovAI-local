import os
import sys
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import huggingface_hub

# Load environment variables
load_dotenv()

# Set the Hugging Face token
hf_token = os.getenv("HF_TOKEN")
if not hf_token:
    print("ERROR: HF_TOKEN environment variable not found!")
    sys.exit(1)

print(f"Using Hugging Face token: {hf_token[:6]}...{hf_token[-4:]}")

# Try to login to Hugging Face
huggingface_hub.login(token=hf_token)

# Try to load the model
try:
    model_name = "sentence-transformers/all-mpnet-base-v2"
    print(f"Loading model: {model_name}")
    model = SentenceTransformer(model_name)
    print("Model loaded successfully!")
    
    # Test the model with a simple sentence
    embeddings = model.encode(["This is a test sentence."])
    print(f"Generated embedding with shape: {embeddings.shape}")
    
except Exception as e:
    print(f"ERROR: Failed to load model: {e}")
    sys.exit(1)

print("All tests passed!") 