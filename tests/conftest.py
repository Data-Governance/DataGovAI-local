import pytest
import os

@pytest.fixture(scope="session")
def storage_doc_content():
    """Fixture to read the content of the storage technologies doc."""
    doc_path = os.path.join(os.path.dirname(__file__), "../docs/01_storage_technologies.md")
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        pytest.fail(f"Test data file not found: {doc_path}")
    except Exception as e:
        pytest.fail(f"Error reading test data file {doc_path}: {e}") 