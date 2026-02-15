import pytest
from memory.vector_memory import VectorMemory

@pytest.fixture
def memory(tmp_path):
    config = {"memory": {"persist_directory": str(tmp_path), "collection_name": "test"}}
    return VectorMemory(config)

def test_add_and_search(memory):
    memory.add("Привет, мир!")
    results = memory.search("мир")
    assert len(results) > 0
    assert "Привет, мир!" in results[0]