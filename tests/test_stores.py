"""
Tests for the storage handlers (DocumentStore, VectorStore, KnowledgeStore).

Note: These tests require mocking the respective database clients (pymongo, pymilvus, neo4j).
"""

import pytest
from unittest.mock import Mock, patch, ANY
import numpy as np

from knowledge_base_agent.storage.document_store import DocumentStore
from knowledge_base_agent.storage.vector_store import VectorStore
from knowledge_base_agent.storage.knowledge_store import KnowledgeStore
from knowledge_base_agent.models import Document, Entity, Relationship

# --- DocumentStore Tests (MongoDB) ---

@patch('knowledge_base_agent.storage.document_store.MongoClient')
def test_document_store_init(MockMongoClient):
    """Test DocumentStore initialization and index creation."""
    mock_client = Mock()
    mock_db = Mock()
    mock_collection = Mock()
    MockMongoClient.return_value = mock_client
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    
    store = DocumentStore()
    
    MockMongoClient.assert_called_once_with(ANY) # Check if called with URI
    mock_collection.create_index.assert_any_call('id', unique=True)
    # Add assertions for other indexes if needed
    assert store.client == mock_client
    assert store.db == mock_db
    assert store.collection == mock_collection

@patch('knowledge_base_agent.storage.document_store.MongoClient')
def test_document_store_store_document(MockMongoClient):
    """Test storing a document."""
    mock_collection = Mock()
    # Simulate insert_one result
    mock_insert_result = Mock()
    mock_insert_result.inserted_id = "mock_mongo_id_123"
    mock_collection.insert_one.return_value = mock_insert_result
    
    # Setup mock client/db to return the mock collection
    mock_client = Mock()
    mock_db = Mock()
    MockMongoClient.return_value = mock_client
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    
    store = DocumentStore()
    doc_data = {"id": "doc1", "content": "Test content", "metadata": {}}
    
    result_id = store.store_document(doc_data)
    
    mock_collection.insert_one.assert_called_once_with(doc_data)
    assert result_id == "mock_mongo_id_123"

@patch('knowledge_base_agent.storage.document_store.MongoClient')
def test_document_store_get_document(MockMongoClient):
    """Test retrieving a document."""
    mock_collection = Mock()
    expected_doc = {"_id": "doc1", "content": "Test content"}
    mock_collection.find_one.return_value = expected_doc
    
    mock_client = Mock()
    mock_db = Mock()
    MockMongoClient.return_value = mock_client
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    
    store = DocumentStore()
    doc = store.get_document("doc1")
    
    mock_collection.find_one.assert_called_once_with({"_id": "doc1"})
    assert doc == expected_doc

@patch('knowledge_base_agent.storage.document_store.MongoClient')
def test_document_store_get_document_not_found(MockMongoClient):
    """Test retrieving a non-existent document."""
    mock_collection = Mock()
    mock_collection.find_one.return_value = None # Simulate not found
    
    mock_client = Mock()
    mock_db = Mock()
    MockMongoClient.return_value = mock_client
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    
    store = DocumentStore()
    doc = store.get_document("non_existent_doc")
    
    mock_collection.find_one.assert_called_once_with({"_id": "non_existent_doc"})
    assert doc is None

@patch('knowledge_base_agent.storage.document_store.MongoClient')
def test_document_store_update_document(MockMongoClient):
    """Test updating a document."""
    mock_collection = Mock()
    updated_doc = {"_id": "doc1", "content": "Updated content"}
    mock_collection.find_one_and_update.return_value = updated_doc
    
    mock_client = Mock()
    mock_db = Mock()
    MockMongoClient.return_value = mock_client
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    
    store = DocumentStore()
    updates = {"content": "Updated content"}
    result = store.update_document("doc1", updates)
    
    from pymongo import ReturnDocument # Import locally for assertion
    mock_collection.find_one_and_update.assert_called_once_with(
        {"_id": "doc1"}, 
        {'$set': updates},
        return_document=ReturnDocument.AFTER
    )
    assert result == updated_doc

@patch('knowledge_base_agent.storage.document_store.MongoClient')
def test_document_store_delete_document(MockMongoClient):
    """Test deleting a document."""
    mock_collection = Mock()
    mock_delete_result = Mock()
    mock_delete_result.deleted_count = 1
    mock_collection.delete_one.return_value = mock_delete_result
    
    mock_client = Mock()
    mock_db = Mock()
    MockMongoClient.return_value = mock_client
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    
    store = DocumentStore()
    deleted = store.delete_document("doc1")
    
    mock_collection.delete_one.assert_called_once_with({"_id": "doc1"})
    assert deleted is True

@patch('knowledge_base_agent.storage.document_store.MongoClient')
def test_document_store_delete_document_not_found(MockMongoClient):
    """Test deleting a non-existent document."""
    mock_collection = Mock()
    mock_delete_result = Mock()
    mock_delete_result.deleted_count = 0 # Simulate not found
    mock_collection.delete_one.return_value = mock_delete_result
    
    mock_client = Mock()
    mock_db = Mock()
    MockMongoClient.return_value = mock_client
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    
    store = DocumentStore()
    deleted = store.delete_document("doc1")
    
    mock_collection.delete_one.assert_called_once_with({"_id": "doc1"})
    assert deleted is False

@patch('knowledge_base_agent.storage.document_store.MongoClient')
def test_document_store_search_documents(MockMongoClient):
    """Test searching documents."""
    mock_collection = Mock()
    mock_cursor = Mock()
    expected_results = [{"_id": "doc1"}, {"_id": "doc2"}]
    mock_cursor.limit.return_value = expected_results # Simulate find().limit()
    mock_collection.find.return_value = mock_cursor
    
    mock_client = Mock()
    mock_db = Mock()
    MockMongoClient.return_value = mock_client
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    
    store = DocumentStore()
    query = {"metadata.type": "test"}
    limit = 5
    results = store.search_documents(query, limit)
    
    mock_collection.find.assert_called_once_with(query)
    mock_cursor.limit.assert_called_once_with(limit)
    assert results == expected_results

@patch('knowledge_base_agent.storage.document_store.MongoClient')
def test_document_store_close(MockMongoClient):
    """Test closing the document store connection."""
    mock_client = Mock()
    MockMongoClient.return_value = mock_client
    
    store = DocumentStore()
    store.close()
    
    mock_client.close.assert_called_once()

# --- VectorStore Tests (Milvus) ---

@patch('knowledge_base_agent.storage.vector_store.MilvusClient')
def test_vector_store_init_and_create_collection(MockMilvusClient):
    """Test VectorStore initialization and collection creation (if not exists)."""
    mock_client = Mock()
    MockMilvusClient.return_value = mock_client
    mock_client.has_collection.return_value = False # Simulate collection doesn't exist
    
    store = VectorStore() # __init__ calls _create_collection
    
    MockMilvusClient.assert_called_once_with(uri=ANY, token=ANY)
    mock_client.has_collection.assert_called_once_with(store.collection_name)
    mock_client.create_collection.assert_called_once_with(
        collection_name=store.collection_name,
        schema=ANY
    )
    mock_client.create_index.assert_called_once_with(
        collection_name=store.collection_name,
        field_name="embedding",
        index_params=ANY
    )
    assert store.client == mock_client

@patch('knowledge_base_agent.storage.vector_store.MilvusClient')
def test_vector_store_init_collection_exists(MockMilvusClient):
    """Test VectorStore initialization when collection already exists."""
    mock_client = Mock()
    MockMilvusClient.return_value = mock_client
    mock_client.has_collection.return_value = True # Simulate collection exists
    
    store = VectorStore()
    
    MockMilvusClient.assert_called_once_with(uri=ANY, token=ANY)
    mock_client.has_collection.assert_called_once_with(store.collection_name)
    mock_client.create_collection.assert_not_called()
    mock_client.create_index.assert_not_called()

@patch('knowledge_base_agent.storage.vector_store.MilvusClient')
def test_vector_store_store_embeddings(MockMilvusClient):
    """Test storing embeddings."""
    mock_client = Mock()
    mock_client.has_collection.return_value = True # Assume collection exists
    mock_insert_result = Mock()
    mock_insert_result.primary_keys = [1, 2]
    mock_client.insert.return_value = mock_insert_result
    MockMilvusClient.return_value = mock_client
    
    store = VectorStore()
    embeddings_data = [
        {'doc_id': "doc1", 'chunk_idx': 0, 'embedding': np.array([0.1, 0.2])},
        {'doc_id': "doc1", 'chunk_idx': 1, 'embedding': np.array([0.3, 0.4])},
    ]
    
    # Convert numpy arrays to lists for assertion comparison
    expected_data_format = {
        "doc_id": ["doc1", "doc1"],
        "chunk_idx": [0, 1],
        "embedding": [[0.1, 0.2], [0.3, 0.4]]
    }
    
    ids = store.store_embeddings(embeddings_data)
    
    mock_client.insert.assert_called_once_with(
        collection_name=store.collection_name,
        data=expected_data_format
    )
    assert ids == [1, 2]

@patch('knowledge_base_agent.storage.vector_store.MilvusClient')
def test_vector_store_search(MockMilvusClient):
    """Test searching for similar embeddings."""
    mock_client = Mock()
    mock_client.has_collection.return_value = True
    # Mock the search result structure
    mock_hit1 = Mock()
    mock_hit1.entity.get.side_effect = lambda key: {'doc_id': "doc1", 'chunk_idx': 5}.get(key)
    mock_hit1.score = 0.95
    mock_hit2 = Mock()
    mock_hit2.entity.get.side_effect = lambda key: {'doc_id': "doc2", 'chunk_idx': 0}.get(key)
    mock_hit2.score = 0.88
    mock_client.search.return_value = [[mock_hit1, mock_hit2]] # Results are nested in a list
    MockMilvusClient.return_value = mock_client
    
    store = VectorStore()
    query_embedding = np.array([0.1, 0.1])
    limit = 2
    
    results = store.search(query_embedding, limit=limit)
    
    mock_client.search.assert_called_once_with(
        collection_name=store.collection_name,
        data=[query_embedding.tolist()],
        field_name="embedding",
        param=ANY, # Default search params
        limit=limit,
        output_fields=["doc_id", "chunk_idx"]
    )
    assert results == [("doc1", 5, 0.95), ("doc2", 0, 0.88)]

@patch('knowledge_base_agent.storage.vector_store.MilvusClient')
def test_vector_store_delete_embeddings(MockMilvusClient):
    """Test deleting embeddings for a document."""
    mock_client = Mock()
    mock_client.has_collection.return_value = True
    MockMilvusClient.return_value = mock_client
    
    store = VectorStore()
    doc_id_to_delete = "doc_to_delete"
    
    deleted = store.delete_embeddings(doc_id_to_delete)
    
    expected_expr = f'doc_id == "{doc_id_to_delete}"'
    mock_client.delete.assert_called_once_with(
        collection_name=store.collection_name,
        expr=expected_expr
    )
    assert deleted is True # Method currently always returns True

@patch('knowledge_base_agent.storage.vector_store.MilvusClient')
def test_vector_store_close(MockMilvusClient):
    """Test closing the vector store connection."""
    mock_client = Mock()
    mock_client.has_collection.return_value = True
    MockMilvusClient.return_value = mock_client
    
    store = VectorStore()
    store.close()
    
    mock_client.close.assert_called_once()

# --- KnowledgeStore Tests (Neo4j) ---

@patch('knowledge_base_agent.storage.knowledge_store.GraphDatabase.driver')
def test_knowledge_store_init(MockDriver):
    """Test KnowledgeStore initialization and schema setup."""
    mock_driver = Mock()
    mock_session = Mock()
    mock_driver.session.return_value.__enter__.return_value = mock_session # Handle context manager
    MockDriver.return_value = mock_driver
    
    store = KnowledgeStore() # __init__ calls _setup_schema
    
    MockDriver.assert_called_once_with(ANY, auth=ANY)
    mock_driver.session.assert_called()
    # Check if constraints were created (at least 2 calls to run)
    assert mock_session.run.call_count >= 2
    assert "CREATE CONSTRAINT" in mock_session.run.call_args_list[0][0][0]
    assert "CREATE CONSTRAINT" in mock_session.run.call_args_list[1][0][0]
    assert store.driver == mock_driver

@patch('knowledge_base_agent.storage.knowledge_store.GraphDatabase.driver')
def test_knowledge_store_store_document(MockDriver):
    """Test storing a document node."""
    mock_driver = Mock()
    mock_session = Mock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    MockDriver.return_value = mock_driver
    
    store = KnowledgeStore()
    doc = Document(id="doc1", title="Test Doc", content="Content preview", source="test")
    
    store.store_document(doc)
    
    mock_session.run.assert_called_once_with(
        ANY, # The Cypher query string
        {
            "id": doc.id,
            "properties": {
                "title": doc.title,
                "content": doc.content[:1000],
                "source": doc.source,
                "created_at": doc.created_at.isoformat(),
                "metadata": doc.metadata
            }
        }
    )
    # Check if the query merges a Document node
    assert "MERGE (d:Document {id: $id})" in mock_session.run.call_args[0][0]

@patch('knowledge_base_agent.storage.knowledge_store.GraphDatabase.driver')
def test_knowledge_store_store_entities(MockDriver):
    """Test storing entities and linking them to a document."""
    mock_driver = Mock()
    mock_session = Mock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    MockDriver.return_value = mock_driver
    
    store = KnowledgeStore()
    doc_id = "doc1"
    entities = [
        Entity(id="e1", type="PERSON", name="Alice", document_id=doc_id),
        Entity(id="e2", type="ORG", name="Acme", document_id=doc_id)
    ]
    
    store.store_entities(doc_id, entities)
    
    # Check that run was called once per entity
    assert mock_session.run.call_count == len(entities)
    # Check args for the first call
    call_args_1 = mock_session.run.call_args_list[0]
    assert "MERGE (e:Entity {id: $entity_id})" in call_args_1[0][0]
    assert "MERGE (e)-[r:APPEARS_IN]->(d)" in call_args_1[0][0]
    assert call_args_1[1] == {
        "entity_id": entities[0].id,
        "type": entities[0].type,
        "name": entities[0].name,
        "metadata": entities[0].metadata,
        "doc_id": doc_id
    }
    # Check args for the second call
    call_args_2 = mock_session.run.call_args_list[1]
    assert call_args_2[1]["entity_id"] == entities[1].id

@patch('knowledge_base_agent.storage.knowledge_store.GraphDatabase.driver')
def test_knowledge_store_store_relationships(MockDriver):
    """Test storing relationships between entities."""
    # Note: This test assumes the KnowledgeStore model Relationship has changed 
    # from from_entity/to_entity to from_entity_id/to_entity_id. 
    # If not, adjust the Relationship instantiation.
    mock_driver = Mock()
    mock_session = Mock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    MockDriver.return_value = mock_driver
    
    store = KnowledgeStore()
    relationships = [
        Relationship(id="r1", from_entity_id="e1", to_entity_id="e2", type="WORKS_AT", document_id="doc1")
    ]
    
    store.store_relationships(relationships)
    
    assert mock_session.run.call_count == len(relationships)
    call_args = mock_session.run.call_args_list[0]
    assert "MERGE (e1)-[r:RELATES_TO {type: $type}]->(e2)" in call_args[0][0]
    assert call_args[1] == {
        "from_id": relationships[0].from_entity_id,
        "to_id": relationships[0].to_entity_id,
        "type": relationships[0].type,
        "metadata": relationships[0].metadata
    }

@patch('knowledge_base_agent.storage.knowledge_store.GraphDatabase.driver')
def test_knowledge_store_query_related_entities(MockDriver):
    """Test querying related entities."""
    mock_driver = Mock()
    mock_session = Mock()
    mock_result = Mock()
    # Simulate result processing (this is complex to mock perfectly)
    mock_node1 = {"id": "e1", "name": "Alice", "type": "PERSON"}
    mock_node2 = {"id": "e2", "name": "Acme", "type": "ORG"}
    mock_rel = {"start_node": mock_node1, "end_node": mock_node2, "type": "WORKS_AT"}
    mock_path = Mock()
    mock_path.nodes = [mock_node1, mock_node2]
    mock_path.relationships = [mock_rel]
    mock_result.__iter__.return_value = iter([{"path": mock_path}]) # Simulate one path result
    mock_session.run.return_value = mock_result
    mock_driver.session.return_value.__enter__.return_value = mock_session
    MockDriver.return_value = mock_driver
    
    store = KnowledgeStore()
    entity_id = "e1"
    max_depth = 1
    
    context = store.query_related_entities(entity_id, max_depth)
    
    mock_session.run.assert_called_once_with(ANY, {"entity_id": entity_id, "max_depth": max_depth})
    assert "MATCH path = (start:Entity {id: $entity_id})-[*1..$max_depth]-(related:Entity)" in mock_session.run.call_args[0][0]
    
    # Check the processed output structure
    assert isinstance(context, dict)
    assert "entities" in context
    assert "relationships" in context
    assert len(context["entities"]) == 2
    assert ("e1", "Alice", "PERSON") in context["entities"]
    assert ("e2", "Acme", "ORG") in context["entities"]
    assert len(context["relationships"]) == 1
    assert context["relationships"][0]["from"] == "e1"
    assert context["relationships"][0]["to"] == "e2"
    assert context["relationships"][0]["type"] == "WORKS_AT"

@patch('knowledge_base_agent.storage.knowledge_store.GraphDatabase.driver')
def test_knowledge_store_get_document_entities(MockDriver):
    """Test getting entities associated with a document."""
    mock_driver = Mock()
    mock_session = Mock()
    mock_result = Mock()
    # Simulate result processing
    mock_record1 = {"e": {"id": "e1", "type": "PERSON", "name": "Alice", "metadata": {}}}
    mock_record2 = {"e": {"id": "e2", "type": "ORG", "name": "Acme", "metadata": {}}}
    mock_result.__iter__.return_value = iter([mock_record1, mock_record2])
    mock_session.run.return_value = mock_result
    mock_driver.session.return_value.__enter__.return_value = mock_session
    MockDriver.return_value = mock_driver
    
    store = KnowledgeStore()
    doc_id = "doc1"
    
    entities = store.get_document_entities(doc_id)
    
    mock_session.run.assert_called_once_with(ANY, {"doc_id": doc_id})
    assert "MATCH (e:Entity)-[:APPEARS_IN]->(d:Document {id: $doc_id})" in mock_session.run.call_args[0][0]
    
    assert len(entities) == 2
    assert isinstance(entities[0], Entity)
    assert entities[0].id == "e1"
    assert entities[0].type == "PERSON"
    assert entities[0].name == "Alice"
    assert entities[1].id == "e2"
    assert entities[1].type == "ORG"

@patch('knowledge_base_agent.storage.knowledge_store.GraphDatabase.driver')
def test_knowledge_store_close(MockDriver):
    """Test closing the knowledge store connection."""
    mock_driver = Mock()
    MockDriver.return_value = mock_driver
    
    store = KnowledgeStore()
    store.close()
    
    mock_driver.close.assert_called_once()

# TODO: Add test_knowledge_store_store_document with mock session
# TODO: Add test_knowledge_store_store_entities with mock session
# TODO: Add test_knowledge_store_store_relationships with mock session
# TODO: Add test_knowledge_store_query_related_entities with mock session
# TODO: Add test_knowledge_store_get_document_entities with mock session
# TODO: Add test_knowledge_store_close 