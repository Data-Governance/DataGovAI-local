import pytest
from knowledge_base_agent.utils.text import (
    clean_text,
    split_into_chunks,
    extract_keywords,
    get_text_stats
)

@pytest.fixture
def sample_text():
    return """
    This is a sample text. It contains multiple sentences!
    Some sentences are short. Others are much longer and contain more information about various topics.
    We need to test text processing capabilities effectively.
    """

def test_clean_text():
    """Test text cleaning functionality."""
    # Test whitespace handling
    assert clean_text("  multiple    spaces  ") == "multiple spaces"
    
    # Test special character removal
    assert clean_text("Hello! @#$%^&* World?") == "Hello! World?"
    
    # Test punctuation preservation
    assert clean_text("Hello, world! How are you?") == "Hello, world! How are you?"

def test_split_into_chunks(sample_text):
    """Test text chunking functionality."""
    chunks = split_into_chunks(
        sample_text,
        max_chunk_size=100,
        min_chunk_size=10,
        overlap_size=20
    )
    
    # Verify chunks
    assert len(chunks) > 0
    for chunk in chunks:
        assert len(chunk) <= 100
        assert len(chunk) >= 10

def test_extract_keywords(sample_text):
    """Test keyword extraction functionality."""
    keywords = extract_keywords(sample_text, max_keywords=5)
    
    # Verify keywords
    assert len(keywords) <= 5
    assert all(isinstance(k, str) for k in keywords)
    assert all(len(k) > 2 for k in keywords)

def test_get_text_stats(sample_text):
    """Test text statistics functionality."""
    stats = get_text_stats(sample_text)
    
    # Verify stats
    assert "char_count" in stats
    assert "word_count" in stats
    assert "sentence_count" in stats
    assert "avg_word_length" in stats
    assert "avg_sentence_length" in stats
    
    # Verify values
    assert stats["char_count"] > 0
    assert stats["word_count"] > 0
    assert stats["sentence_count"] > 0
    assert stats["avg_word_length"] > 0
    assert stats["avg_sentence_length"] > 0

def test_edge_cases():
    """Test edge cases in text processing."""
    # Empty text
    assert clean_text("") == ""
    assert split_into_chunks("") == []
    assert extract_keywords("") == []
    
    # Single word
    single_word = "Hello"
    assert clean_text(single_word) == single_word
    assert len(split_into_chunks(single_word)) <= 1
    
    # Very long text
    long_text = "word " * 1000
    chunks = split_into_chunks(long_text, max_chunk_size=100)
    assert all(len(chunk) <= 100 for chunk in chunks)

def test_chunk_overlap():
    """Test that chunks properly overlap."""
    text = "Sentence one. Sentence two. Sentence three. Sentence four."
    chunks = split_into_chunks(
        text,
        max_chunk_size=30,
        min_chunk_size=10,
        overlap_size=15
    )
    
    if len(chunks) > 1:
        # Check that consecutive chunks share some content
        for i in range(len(chunks) - 1):
            current = chunks[i]
            next_chunk = chunks[i + 1]
            # Either the end of current chunk should appear at start of next
            # or start of next should appear at end of current
            overlap_exists = (
                current[-15:] in next_chunk or
                next_chunk[:15] in current
            )
            assert overlap_exists 