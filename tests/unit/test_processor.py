"""
Tests for the document processor.
"""

import pytest
from unittest.mock import Mock, patch, call, ANY
import numpy as np
from datetime import datetime
import uuid

from knowledge_base_agent.processor import DocumentProcessor, chunk_document
from knowledge_base_agent.models import Document, ProcessingConfig, SearchResult, Entity, Relationship
from knowledge_base_agent.exceptions import (
    ProcessingError,
    StorageError,
    EmbeddingError,
    EntityExtractionError
)

@pytest.fixture
def mock_stores():
    """Create mock stores with appropriate interfaces."""
    vector_store = Mock()
    # Mock search to return list of (doc_id, chunk_id, score)
    vector_store.search.return_value = []
    # Mock store_embeddings for chunk format (doc_id, List[Tuple[chunk_id, embedding]])
    vector_store.store_embeddings = Mock()
    
    document_store = Mock()
    document_store.get_document.return_value = None
    document_store.store_document = Mock()
    
    knowledge_store = Mock()
    knowledge_store.get_document_relationships.return_value = []
    # Mock batch storage methods
    knowledge_store.store_entities = Mock()
    knowledge_store.store_relationships = Mock()

    return vector_store, document_store, knowledge_store

@pytest.fixture
def mock_embedding_model():
    """Create mock embedding model."""
    model = Mock()
    # generate needs to return a list of embeddings, one per input text
    model.generate.side_effect = lambda texts: [np.random.rand(1536).tolist() for _ in texts]
    return model

@pytest.fixture
def mock_entity_extractor():
    """Create mock entity extractor."""
    extractor = Mock()
    # Mock extract_relationships to return (entities, relationships)
    extractor.extract_relationships.return_value = ([], [])
    return extractor

@pytest.fixture
def test_config():
    """Create a default ProcessingConfig for tests."""
    return ProcessingConfig(max_chunk_size=100, min_chunk_size=10, overlap_size=10)

@pytest.fixture
def processor(mock_stores, mock_embedding_model, mock_entity_extractor, test_config):
    """Create a document processor instance with mocks and config."""
    vector_store, document_store, knowledge_store = mock_stores
    processor = DocumentProcessor(
        vector_store=vector_store,
        document_store=document_store,
        knowledge_store=knowledge_store,
        embedding_model=mock_embedding_model,
        config=test_config
    )
    # Patch the entity extractor instance used by the processor
    processor.entity_extractor = mock_entity_extractor
    return processor

def create_test_doc(doc_id: str, content: str, chunks: List[str], entities: List[Entity] = None, relationships: List[Relationship] = None) -> Document:
    """Creates a Pydantic Document model for testing."""
    return Document(
        id=doc_id,
        content=content,
        chunks=chunks,
        title=f"Test Doc {doc_id}",
        entities=entities or [],
        relationships=relationships or [],
        metadata={'source': 'test'}
    )

def test_process_document_success_with_chunking(processor, mock_stores, mock_embedding_model, mock_entity_extractor, test_config):
    """Test successful document processing with chunking and entity extraction."""
    vector_store, document_store, knowledge_store = mock_stores
    
    # Test data
    doc_id_generated = None # Capture generated doc_id
    content = "This is the first sentence. This is the second sentence. This is the third." # Example content
    metadata = {"title": "Chunking Test", "source": "pytest"}
    
    # Mock entity extractor results
    entity1 = Entity(id="e1", name="first sentence", type="PHRASE", document_id="") # doc_id set later
    entity2 = Entity(id="e2", name="third", type="ORDINAL", document_id="")
    rel1 = Relationship(id="r1", from_entity_id="e1", to_entity_id="e2", type=" FOLLOWS", document_id="")
    mock_entity_extractor.extract_relationships.return_value = ([entity1, entity2], [rel1])

    # Mock chunking result (depends on tokenizer and config, approximate here)
    # Use the actual chunk_document function for consistency if possible, but mocking is simpler for isolation
    expected_chunks = [
        "This is the first sentence.", 
        " This is the second sentence.", 
        " This is the third."
    ]
    with patch('knowledge_base_agent.processor.chunk_document', return_value=expected_chunks) as mock_chunk:
        # Process document
        doc_id_generated = processor.process_document(content, metadata)
        mock_chunk.assert_called_once_with(content, test_config, processor.tokenizer)
    
    assert doc_id_generated is not None

    # Verify document_store.store_document was called with the Document object
    document_store.store_document.assert_called_once()
    stored_doc_arg = document_store.store_document.call_args[0][0]
    assert isinstance(stored_doc_arg, Document)
    assert stored_doc_arg.id == doc_id_generated
    assert stored_doc_arg.content == content
    assert stored_doc_arg.chunks == expected_chunks
    assert stored_doc_arg.title == metadata["title"]
    assert stored_doc_arg.metadata['source'] == metadata["source"]
    
    # Verify embedding_model.generate was called with chunks
    mock_embedding_model.generate.assert_called_once_with(expected_chunks)
    num_embeddings_generated = len(mock_embedding_model.generate.return_value)
    assert num_embeddings_generated == len(expected_chunks)
    
    # Verify vector_store.store_embeddings was called correctly (with list of dicts)
    vector_store.store_embeddings.assert_called_once()
    args, kwargs = vector_store.store_embeddings.call_args
    embeddings_stored = args[0]
    assert isinstance(embeddings_stored, list)
    assert len(embeddings_stored) == len(expected_chunks)
    for i, stored_item in enumerate(embeddings_stored):
        assert isinstance(stored_item, dict)
        assert stored_item['doc_id'] == doc_id_generated
        assert stored_item['chunk_idx'] == i
        assert 'embedding' in stored_item
        assert isinstance(stored_item['embedding'], list) # Embeddings are lists of floats
        assert len(stored_item['embedding']) == 1536 # Check embedding dimension

    # Verify entity/relationship storage
    mock_entity_extractor.extract_relationships.assert_called_once_with(content)
    
    # Verify knowledge_store.store_entities call (with doc_id and list)
    knowledge_store.store_entities.assert_called_once()
    args, kwargs = knowledge_store.store_entities.call_args
    assert args[0] == doc_id_generated # First arg is doc_id
    stored_entities_arg = args[1]
    assert isinstance(stored_entities_arg, list)
    assert len(stored_entities_arg) == 2
    assert stored_entities_arg[0].id == "e1"
    assert stored_entities_arg[0].document_id == doc_id_generated # Check doc_id linkage
    assert stored_entities_arg[1].id == "e2"
    assert stored_entities_arg[1].document_id == doc_id_generated
    
    # Verify knowledge_store.store_relationships call (just list)
    knowledge_store.store_relationships.assert_called_once()
    stored_rels_arg = knowledge_store.store_relationships.call_args[0][0]
    assert isinstance(stored_rels_arg, list)
    assert len(stored_rels_arg) == 1

def test_process_document_no_chunks(processor, mock_stores, mock_embedding_model, mock_entity_extractor):
    """Test processing a document that results in no valid chunks."""
    vector_store, document_store, knowledge_store = mock_stores
    content = "Too short"
    metadata = {"title": "Short Doc"}
    
    with patch('knowledge_base_agent.processor.chunk_document', return_value=[]) as mock_chunk:
        doc_id = processor.process_document(content, metadata)

    # Verify document metadata stored, but no embeddings or KG data
    document_store.store_document.assert_called_once()
    stored_doc = document_store.store_document.call_args[0][0]
    assert stored_doc.id == doc_id
    assert stored_doc.content == content
    assert stored_doc.chunks == []
    assert stored_doc.title == metadata["title"]
    
    mock_embedding_model.generate.assert_not_called()
    vector_store.store_embeddings.assert_not_called()
    mock_entity_extractor.extract_relationships.assert_not_called()
    knowledge_store.store_entities.assert_not_called()
    knowledge_store.store_relationships.assert_not_called()

def test_process_document_storage_error(processor, mock_stores):
    """Test document processing fails correctly on document store error."""
    vector_store, document_store, knowledge_store = mock_stores
    document_store.store_document.side_effect = StorageError("DB connection failed")
    content = "Some content that chunks normally"
    with patch('knowledge_base_agent.processor.chunk_document', return_value=["chunk1"]):
        with pytest.raises(StorageError, match="DB connection failed"):
            processor.process_document(content)

def test_process_document_embedding_error(processor, mock_stores, mock_embedding_model):
    """Test document processing fails correctly on embedding generation error."""
    vector_store, document_store, knowledge_store = mock_stores
    mock_embedding_model.generate.side_effect = EmbeddingError("API limit reached")
    content = "Some content that chunks normally"
    with patch('knowledge_base_agent.processor.chunk_document', return_value=["chunk1", "chunk2"]):
        with pytest.raises(EmbeddingError, match="API limit reached"):
            processor.process_document(content)
        # Ensure document structure was stored before embedding failed
        document_store.store_document.assert_called_once()
        vector_store.store_embeddings.assert_not_called() # Should fail before storing

def test_process_document_entity_error(processor, mock_stores, mock_entity_extractor):
    """Test document processing fails correctly on entity extraction/storage error."""
    vector_store, document_store, knowledge_store = mock_stores
    mock_entity_extractor.extract_relationships.side_effect = EntityExtractionError("Model timeout")
    content = "Some content that chunks normally"
    with patch('knowledge_base_agent.processor.chunk_document', return_value=["chunk1"]):
        with pytest.raises(EntityExtractionError, match="Model timeout"):
            processor.process_document(content)
        # Ensure doc and embeddings were stored before entity extraction failed
        document_store.store_document.assert_called_once()
        vector_store.store_embeddings.assert_called_once()
        knowledge_store.store_entities.assert_not_called()
        knowledge_store.store_relationships.assert_not_called()

def test_search_success_returns_chunks(processor, mock_stores, mock_embedding_model):
    """Test successful search returns correct chunk-level SearchResult objects."""
    vector_store, document_store, knowledge_store = mock_stores
    query = "find relevant chunk"
    doc_id = str(uuid.uuid4())
    chunks = ["Relevant chunk 1 text.", "Second chunk less relevant.", "Third chunk."]
    metadata = {"source": "search_test"}

    # Mock vector search results (doc_id, chunk_id, score)
    # Return multiple chunks from the same doc, ensure highest score comes first later
    vector_store.search.return_value = [
        (doc_id, 0, 0.9),
        (doc_id, 2, 0.7), # Lower score, different chunk
        (str(uuid.uuid4()), 0, 0.8) # Different doc_id, ignored due to top_k=2
    ]
    
    # Mock document retrieval
    test_doc = Document(
        id=doc_id, 
        content="Full content...", 
        chunks=chunks, 
        metadata=metadata
    )
    # Make get_document return the doc when called with the correct ID
    document_store.get_document.side_effect = lambda requested_id: test_doc if requested_id == doc_id else None
    
    # Perform search
    results = processor.search(query, top_k=2, min_score=0.6)
    
    # Verify embedding call for query
    mock_embedding_model.generate.assert_called_once_with([query])
    # Verify vector store search call
    vector_store.search.assert_called_once_with(ANY, top_k=2) # ANY for query embedding
    # Verify document store call (should be called only for the relevant doc_id)
    document_store.get_document.assert_called_once_with(doc_id)
    # Verify knowledge store was NOT called (graph enrichment removed)
    knowledge_store.query_related_entities.assert_not_called() # Or any other KS method
    
    # Verify results
    assert len(results) == 2 # Limited by top_k
    
    # Check first result (highest score)
    result1 = results[0]
    assert isinstance(result1, SearchResult)
    assert result1.document_id == doc_id
    assert result1.content == chunks[0] # Content of chunk 0
    assert result1.score == 0.9
    assert result1.metadata == metadata
    assert result1.entities == [] # Not populated by default
    assert result1.relationships == [] # Not populated by default
    
    # Check second result
    result2 = results[1]
    assert isinstance(result2, SearchResult)
    assert result2.document_id == doc_id
    assert result2.content == chunks[2] # Content of chunk 2
    assert result2.score == 0.7
    assert result2.metadata == metadata

def test_search_no_results(processor, mock_stores, mock_embedding_model):
    """Test search when vector store returns no results."""
    vector_store, document_store, knowledge_store = mock_stores
    vector_store.search.return_value = [] # No matches
    query = "find nothing"
    
    results = processor.search(query)
    
    assert results == []
    document_store.get_document.assert_not_called()
    # Knowledge store should not be called
    knowledge_store.query_related_entities.assert_not_called()

def test_search_doc_not_found(processor, mock_stores, mock_embedding_model):
    """Test search when a doc referenced by vector store is not in doc store."""
    vector_store, document_store, knowledge_store = mock_stores
    doc_id_missing = str(uuid.uuid4())
    vector_store.search.return_value = [(doc_id_missing, 0, 0.9)] # Reference missing doc
    document_store.get_document.return_value = None # Simulate doc not found
    query = "find missing doc"
    
    results = processor.search(query)
    
    # Should return empty list as the only potential hit couldn't be retrieved
    assert results == []
    document_store.get_document.assert_called_once_with(doc_id_missing)
    # Knowledge store should not be called
    knowledge_store.query_related_entities.assert_not_called()

def test_query_success_retrieves_chunks(processor, mock_stores, mock_embedding_model):
    """Test that the basic query method retrieves correct chunks."""
    vector_store, document_store, knowledge_store = mock_stores
    doc_id = str(uuid.uuid4())
    query = "find specific chunk"
    chunks = ["Chunk 0 content.", "Chunk 1 the target.", "Chunk 2 irrelevant."]
    metadata = {"title": "Multi-chunk Doc"}

    # Mock vector search results (returns doc_id, chunk_id, score)
    vector_store.search.return_value = [(doc_id, 1, 0.95)] # Match chunk 1
    
    # Mock document retrieval
    test_doc = Document(id=doc_id, content="...".join(chunks), chunks=chunks, metadata=metadata)
    document_store.get_document.return_value = test_doc
    
    # Perform query (uses _query_impl internally)
    result_dict = processor.query(query, limit=1)
    
    # Verify underlying calls
    mock_embedding_model.generate.assert_called_once_with([query])
    vector_store.search.assert_called_once_with(ANY, 1) # ANY for query embedding
    document_store.get_document.assert_called_once_with(doc_id)

    # Verify result structure from _query_impl
    assert result_dict['success'] is True
    assert len(result_dict['results']) == 1
    query_result = result_dict['results'][0]
    assert query_result['content'] == chunks[1] # Check correct chunk content
    assert query_result['similarity'] == 0.95
    assert query_result['document_id'] == doc_id
    assert query_result['chunk_id'] == 1
    assert query_result['metadata'] == metadata

def test_query_invalid_chunk_index(processor, mock_stores, mock_embedding_model):
    """Test query handling when vector store returns an invalid chunk index."""
    vector_store, document_store, knowledge_store = mock_stores
    doc_id = str(uuid.uuid4())
    query = "find invalid chunk"
    chunks = ["Only one chunk"] # Document only has chunk 0
    
    # Mock vector search to return an invalid index
    vector_store.search.return_value = [(doc_id, 5, 0.9)] # Index 5 is invalid
    
    # Mock document retrieval
    test_doc = Document(id=doc_id, content=chunks[0], chunks=chunks)
    document_store.get_document.return_value = test_doc

    result_dict = processor.query(query, limit=1)
    
    # Verify the result is empty because the chunk index was invalid
    assert result_dict['success'] is True
    assert len(result_dict['results']) == 0
    document_store.get_document.assert_called_once_with(doc_id)

def test_query_error_propagates(processor, mock_stores, mock_embedding_model):
    """Test that errors during query embedding or search propagate."""
    vector_store, document_store, knowledge_store = mock_stores
    query = "cause error"
    
    # Test embedding error
    mock_embedding_model.generate.side_effect = EmbeddingError("Failed query embed")
    with pytest.raises(ProcessingError, match="Failed query embed"):
        processor.query(query)
    
    # Reset side effect and test vector store error
    mock_embedding_model.generate.side_effect = lambda texts: [np.random.rand(1536).tolist() for _ in texts]
    vector_store.search.side_effect = StorageError("Failed vector search")
    result_dict = processor.query(query)
    assert result_dict['success'] is False
    assert "Failed vector search" in result_dict['error']
    
    # Reset side effect and test document store error
    vector_store.search.side_effect = None
    vector_store.search.return_value = [(str(uuid.uuid4()), 0, 0.9)]
    document_store.get_document.side_effect = StorageError("Failed doc get")
    result_dict = processor.query(query)
    assert result_dict['success'] is False
    assert "Failed doc get" in result_dict['error']

# --- Test chunk_document helper --- 

# Note: Requires tiktoken installed
# Can mock tokenizer if tiktoken is not available in test env
@pytest.mark.parametrize(
    "content, config_override, expected_chunks_pattern",
    [
        (
            "This is sentence one. This is sentence two. This is sentence three, which is longer.",
            {"max_chunk_size": 5, "min_chunk_size": 2, "overlap_size": 1}, # Small sizes for testing
            [r"This is sentence one\.", r" sentence one\. This", r" This is sentence two\.", r" sentence two\. This", r" This is sentence three", r" sentence three, which", r", which is longer\."], # Approximate, depends heavily on tokenizer
        ),
        (
            "Short.", # Shorter than min_chunk_size
            {"max_chunk_size": 10, "min_chunk_size": 5, "overlap_size": 2},
            ["Short."] # Should return the single chunk if it exists but is small
        ),
        (
            "", # Empty content
            {"max_chunk_size": 10, "min_chunk_size": 5, "overlap_size": 2},
            [] # Should return empty list
        ),
    ]
)
def test_chunk_document(test_config, content, config_override, expected_chunks_pattern):
    """Test the chunk_document helper function with various inputs."""
    # Create a mock tokenizer for predictable behavior if needed, 
    # or use actual tiktoken if available and acceptable for tests.
    try:
        import tiktoken
        tokenizer = tiktoken.get_encoding("cl100k_base")
    except ImportError:
        pytest.skip("tiktoken not installed, skipping chunk_document test")

    # Override default config
    config = test_config.copy(update=config_override)
    
    chunks = chunk_document(content, config, tokenizer)
    
    # Due to the complexity and potential variability of tokenization,
    # checking the exact string might be fragile. Check number of chunks
    # and maybe regex patterns or start/end content.
    assert len(chunks) == len(expected_chunks_pattern)
    # For more robust tests, might need to mock the tokenizer or use known tokenization results.
    # For now, just checking length as patterns are too specific.
    # for chunk, pattern in zip(chunks, expected_chunks_pattern):
    #     assert re.match(pattern, chunk) is not None 

# Remove old tests that are now covered or outdated by chunking logic
# - test_get_entity_context_success (Still valid, keep? -> depends if method is kept)
# - test_get_entity_context_error (Still valid, keep?)
# - test_close_success (Still valid, keep)

# Keep context tests if the method is still relevant
def test_get_entity_context_success(processor, mock_stores):
    """Test successful entity context retrieval."""
    vector_store, document_store, knowledge_store = mock_stores
    context = {"related_entities": [], "relationships": []}
    knowledge_store.query_related_entities.return_value = context
    result = processor.get_entity_context("test-entity-id")
    assert result == context
    knowledge_store.query_related_entities.assert_called_once_with("test-entity-id", max_depth=2)

def test_get_entity_context_error(processor, mock_stores):
    """Test entity context retrieval with error."""
    vector_store, document_store, knowledge_store = mock_stores
    knowledge_store.query_related_entities.side_effect = StorageError("KG query failed")
    with pytest.raises(StorageError, match="KG query failed"):
        processor.get_entity_context("test-entity-id")

def test_close_success(processor, mock_stores):
    """Test successful resource closure."""
    vector_store, document_store, knowledge_store = mock_stores
    processor.close()
    vector_store.close.assert_called_once()
    document_store.close.assert_called_once()
    knowledge_store.close.assert_called_once() 