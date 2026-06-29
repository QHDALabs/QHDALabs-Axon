from collections import defaultdict

from axon.verification.tier0_generator import PilotConfig, SpreadMode, build_world


def _by_id(documents):
    return {doc.doc_id: doc for doc in documents}


def test_width_changes_no_document_count_or_background_document():
    world = build_world(0, PilotConfig(n_peers=19, documents_per_literature=8,
                                       background_documents_per_topic=8))
    zero = _by_id(world.documents_for_width(0, SpreadMode.SYMMETRIC))
    full = _by_id(world.documents_for_width(19, SpreadMode.SYMMETRIC))
    assert zero.keys() == full.keys()
    for doc_id, before in zero.items():
        after = full[doc_id]
        if before.literature in world.background_labels:
            assert after == before


def test_width_uses_nested_frozen_peer_prefixes():
    world = build_world(2, PilotConfig(n_peers=19, documents_per_literature=8,
                                       background_documents_per_topic=8))
    width_one = _by_id(world.documents_for_width(1, SpreadMode.A_ONLY))
    width_two = _by_id(world.documents_for_width(2, SpreadMode.A_ONLY))
    first = world.permutation_a[0]
    second = world.permutation_a[1]
    assert any(term.startswith("mechanism_") for doc_id, doc in width_one.items()
               if doc.literature == first for term in doc.mesh)
    assert not any(term.startswith("mechanism_") for doc_id, doc in width_one.items()
                   if doc.literature == second for term in doc.mesh)
    assert any(term.startswith("mechanism_") for doc_id, doc in width_two.items()
               if doc.literature == second for term in doc.mesh)


def test_non_mechanism_terms_are_never_removed_when_width_increases():
    world = build_world(4, PilotConfig(n_peers=19, documents_per_literature=8,
                                       background_documents_per_topic=8))
    zero = _by_id(world.documents_for_width(0, SpreadMode.SYMMETRIC))
    full = _by_id(world.documents_for_width(19, SpreadMode.SYMMETRIC))
    for doc_id, before in zero.items():
        before_non_m = {term for term in before.mesh if not term.startswith("mechanism_")}
        after_non_m = {term for term in full[doc_id].mesh if not term.startswith("mechanism_")}
        assert before_non_m == after_non_m


def test_spread_modes_touch_only_the_declared_side():
    world = build_world(5, PilotConfig(n_peers=19, documents_per_literature=8,
                                       background_documents_per_topic=8))
    counts = defaultdict(int)
    for doc in world.documents_for_width(19, SpreadMode.A_ONLY):
        if doc.literature.startswith("peer_"):
            counts[doc.literature] += sum(t.startswith("mechanism_") for t in doc.mesh)
    assert all(counts[peer] > 0 for peer in world.peers_a)
    assert all(counts[peer] == 0 for peer in world.peers_c)


def test_background_guarantees_mechanism_common_pool_eligibility():
    config = PilotConfig(n_peers=19, documents_per_literature=8,
                         background_documents_per_topic=20,
                         background_mechanism_rate=0.25)
    world = build_world(7, config)
    background = [doc for doc in world.base_documents
                  if doc.literature in world.background_labels]
    for term_index in range(config.mechanism_terms):
        term = f"mechanism_{term_index}"
        df = sum(term in doc.mesh for doc in background)
        assert df > 0
        assert df / len(background) <= 0.5


def test_peer_document_imbalance_does_not_change_endpoint_or_background_counts():
    config = PilotConfig(n_peers=19, documents_per_literature=10,
                         peer_document_ratio=0.5,
                         background_documents_per_topic=8)
    world = build_world(8, config)
    counts = defaultdict(int)
    for doc in world.base_documents:
        counts[doc.literature] += 1
    assert counts["endpoint_a"] == 10
    assert counts["endpoint_c"] == 10
    assert all(counts[peer] == 5 for peer in world.peers_a + world.peers_c)
    assert all(counts[label] == 8 for label in world.background_labels)
