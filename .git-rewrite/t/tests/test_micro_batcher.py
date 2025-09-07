import pytest

@pytest.mark.sprint_c
def test_micro_batcher_groups_items_deterministically():
    """Micro-batching should split work into predictable batch sizes."""
    def micro_batch(items, batch_size):
        # Simple, deterministic splitter used for scaffolding
        for i in range(0, len(items), batch_size):
            yield items[i:i+batch_size]

    items = list(range(10))
    batches = list(micro_batch(items, batch_size=4))

    # Expect 3 batches: 4, 4, 2
    assert [len(b) for b in batches] == [4, 4, 2]
    # No duplication or loss
    flattened = [x for b in batches for x in b]
    assert flattened == items
