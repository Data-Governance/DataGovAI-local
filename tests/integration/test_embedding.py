from sentence_transformers import SentenceTransformer
import torch
import time

def test_embedding():
    # Print system info
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
    
    # Load model
    print("\nLoading model all-mpnet-base-v2...")
    model = SentenceTransformer('all-mpnet-base-v2', device='cuda' if torch.cuda.is_available() else 'cpu')
    
    # Test sentences
    sentences = [
        "This is a test sentence for embedding generation.",
        "Another sentence to verify GPU acceleration.",
        "Testing batch processing capabilities."
    ]
    
    # Time the embedding generation
    print("\nGenerating embeddings...")
    start_time = time.time()
    embeddings = model.encode(sentences)
    end_time = time.time()
    
    print(f"\nEmbedding shape: {embeddings.shape}")
    print(f"Time taken: {end_time - start_time:.2f} seconds")
    print(f"Average time per sentence: {(end_time - start_time) / len(sentences):.2f} seconds")

if __name__ == "__main__":
    test_embedding() 