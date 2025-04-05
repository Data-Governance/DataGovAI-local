"""
Integration tests for the CLI commands.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock, ANY
import os

# Assuming the main CLI entry point is defined correctly
from knowledge_base_agent.__main__ import cli
from knowledge_base_agent.models import SearchResult
from knowledge_base_agent.exceptions import ProcessingError, StorageError

@pytest.fixture
def runner():
    return CliRunner()

# Use patch to replace the create_processor function during tests
@patch('knowledge_base_agent.__main__.create_processor')
def test_cli_process_success(mock_create_processor, runner):
    """Test successful document processing via CLI."""
    # Mock the processor instance that create_processor will return
    mock_processor = Mock()
    expected_doc_id = "cli-doc-123"
    mock_processor.process_document.return_value = expected_doc_id
    mock_create_processor.return_value = mock_processor
    
    # Create a temporary file to process
    test_content = "This is content from a test file."
    with runner.isolated_filesystem():
        with open("test_doc.txt", "w") as f:
            f.write(test_content)
        
        # Invoke the CLI command
        result = runner.invoke(cli, ['process', 'test_doc.txt', '--title', 'CLIDoc', '--source', 'cli_test'])
        
        # Verify output and exit code
        assert result.exit_code == 0
        assert f"Successfully processed document. ID: {expected_doc_id}" in result.output
        
        # Verify create_processor was called (implicitly tests config loading)
        mock_create_processor.assert_called_once()
        
        # Verify the processor method was called with correct args
        expected_metadata = {'title': 'CLIDoc', 'source': 'cli_test'}
        mock_processor.process_document.assert_called_once_with(test_content, expected_metadata)

@patch('knowledge_base_agent.__main__.create_processor')
def test_cli_process_file_not_found(mock_create_processor, runner):
    """Test CLI process command when file doesn't exist."""
    # No need to mock the processor as the file open should fail first
    result = runner.invoke(cli, ['process', 'non_existent_file.txt'])
    
    # Verify output and exit code
    assert result.exit_code != 0 # Should fail
    assert "Error:" in result.output 
    assert "No such file or directory" in result.output # Check for file system error
    mock_create_processor.assert_not_called() # Processor shouldn't be created if file read fails

@patch('knowledge_base_agent.__main__.create_processor')
def test_cli_process_processor_error(mock_create_processor, runner):
    """Test CLI process command when processor raises an error."""
    mock_processor = Mock()
    error_message = "Processor failed during CLI process"
    mock_processor.process_document.side_effect = ProcessingError(error_message)
    mock_create_processor.return_value = mock_processor
    
    with runner.isolated_filesystem():
        with open("test_doc.txt", "w") as f:
            f.write("Some content")
        
        result = runner.invoke(cli, ['process', 'test_doc.txt'])
        
        # Verify output and exit code
        assert result.exit_code != 0 # Should indicate failure (implicitly via exception)
        assert f"Error: {error_message}" in result.output
        mock_processor.process_document.assert_called_once()

@patch('knowledge_base_agent.__main__.create_processor')
def test_cli_search_success(mock_create_processor, runner):
    """Test successful search via CLI."""
    mock_processor = Mock()
    # Mock search results (list of SearchResult objects)
    mock_results = [
        SearchResult(document_id="doc1", content="Result one content.", score=0.9, metadata={}),
        SearchResult(document_id="doc2", content="Result two content.", score=0.8, metadata={})
    ]
    mock_processor.search.return_value = mock_results
    mock_create_processor.return_value = mock_processor
    
    query = "find stuff via cli"
    limit = 5
    result = runner.invoke(cli, ['search', query, '--limit', str(limit)])
    
    # Verify output and exit code
    assert result.exit_code == 0
    assert "Result 1 (Score: 0.90):" in result.output
    assert f"Content: {mock_results[0].content[:200]}..." in result.output
    assert "Result 2 (Score: 0.80):" in result.output
    assert f"Content: {mock_results[1].content[:200]}..." in result.output
    
    # Verify processor call (uses default min_score and use_graph)
    mock_processor.search.assert_called_once_with(query, top_k=limit)

@patch('knowledge_base_agent.__main__.create_processor')
def test_cli_search_no_results(mock_create_processor, runner):
    """Test CLI search when no results are found."""
    mock_processor = Mock()
    mock_processor.search.return_value = [] # No results
    mock_create_processor.return_value = mock_processor
    
    query = "find nothing"
    result = runner.invoke(cli, ['search', query])
    
    # Verify output and exit code
    assert result.exit_code == 0
    assert "Result 1" not in result.output # Check that no result output is printed
    mock_processor.search.assert_called_once_with(query, top_k=5) # Default limit

@patch('knowledge_base_agent.__main__.create_processor')
def test_cli_search_processor_error(mock_create_processor, runner):
    """Test CLI search when processor raises an error."""
    mock_processor = Mock()
    error_message = "Search failed during CLI search"
    mock_processor.search.side_effect = StorageError(error_message)
    mock_create_processor.return_value = mock_processor
    
    query = "cause search error"
    result = runner.invoke(cli, ['search', query])
    
    # Verify output and exit code
    assert result.exit_code != 0 # Implicit failure
    assert f"Error: {error_message}" in result.output
    mock_processor.search.assert_called_once_with(query, top_k=5) 