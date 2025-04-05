from sentence_transformers import SentenceTransformer
import os

print('Starting model download...')
# Find the model cache directory used by sentence-transformers
print('Using cpu to download model to ensure compatibility')
model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
print(f'Model successfully downloaded and cached!')
print(f'Model dimension: {model.get_sentence_embedding_dimension()}')
print("You can now run the processing with GPU acceleration") 