"""Black-box tests for classical propositional semantics, K01–K05."""

import pytest

from react_sudoku.knowledge import KnowledgeBase


def query(kb, literal):
    result = kb.query(literal)
    assert result["ok"] is True
    return result["data"]["result"]


@pytest.mark.parametrize("literal", ["", "~", "~~A", " A", "A B", "A&B", "1A", "é", "A" * 65, True, None])
def test_k01_invalid_literals(literal):
    kb = KnowledgeBase()
    assert kb.add_fact(literal)["code"] == "invalid_literal"
    assert kb.query(literal)["code"] == "invalid_literal"
    assert query(kb, "A") == "unresolved"


@pytest.mark.parametrize("literal", ["A", "~A", "a_12", "A" * 64])
def test_k01_literal_boundaries(literal):
    kb = KnowledgeBase()
    assert kb.add_fact(literal)["ok"]
    assert query(kb, literal) == "entailed"


def test_k03_k04_fact_query_duplicate_and_atomic_rollback():
    kb = KnowledgeBase()
    assert query(kb, "A") == "unresolved"
    assert kb.add_fact("A")["data"]["changed"] is True
    assert kb.add_fact("A")["data"]["changed"] is False
    assert query(kb, "A") == "entailed"
    assert query(kb, "~A") == "contradicted"
    assert query(kb, "a") == "unresolved"
    assert kb.add_fact("~A")["code"] == "inconsistent_kb"
    assert query(kb, "A") == "entailed"


def test_k02_k04_conjunction_chains_and_negative_premises():
    kb = KnowledgeBase()
    assert kb.add_rule(["A", "~B"], "C")["ok"]
    assert kb.add_rule(["C"], "D")["ok"]
    assert kb.add_fact("A")["ok"]
    assert query(kb, "C") == "unresolved"
    assert kb.add_fact("~B")["ok"]
    assert query(kb, "D") == "entailed"


def test_k04_classical_contraposition():
    kb = KnowledgeBase()
    kb.add_rule(["A"], "B")
    kb.add_fact("~B")
    assert query(kb, "A") == "contradicted"
    assert query(kb, "~A") == "entailed"


def test_k03_inconsistent_rule_rolls_back_all_its_effects():
    kb = KnowledgeBase()
    kb.add_fact("A")
    kb.add_fact("~B")
    assert kb.add_rule(["A"], "B")["code"] == "inconsistent_kb"
    assert query(kb, "A") == "entailed"
    assert query(kb, "B") == "contradicted"
    assert kb.add_rule(["A"], "C")["ok"]


def test_k03_rule_premises_are_canonicalized():
    kb = KnowledgeBase()
    assert kb.add_rule(["A", "B"], "C")["data"]["changed"] is True
    assert kb.add_rule(["B", "A", "A"], "C")["data"]["changed"] is False


@pytest.mark.parametrize("premises,head", [([], "A"), (["A"] * 10, "B"), ("A", "B"), (["~~A"], "B"), (["A"], "")])
def test_k02_invalid_rule(premises, head):
    kb = KnowledgeBase()
    assert kb.add_rule(premises, head)["ok"] is False
    assert query(kb, "B") == "unresolved"


def test_k05_atom_limit_and_queries_do_not_consume_capacity():
    kb = KnowledgeBase()
    for i in range(70):
        assert query(kb, f"Unknown{i}") == "unresolved"
    for i in range(64):
        assert kb.add_fact(f"A{i}")["ok"]
    assert kb.add_fact("Overflow")["code"] == "kb_limit"
    assert query(kb, "Overflow") == "unresolved"
    assert kb.add_fact("A0")["data"]["changed"] is False


def test_k05_statement_limit_is_atomic():
    kb = KnowledgeBase()
    # Distinct tautologies stay satisfiable and use only 16 atoms.
    for i in range(16):
        for j in range(16):
            assert kb.add_rule([f"A{i}", f"A{j}"], f"A{i}")["ok"]
    assert kb.add_fact("A0")["code"] == "kb_limit"
    assert query(kb, "A0") == "unresolved"
    assert kb.add_rule(["A0"], "A0")["data"]["changed"] is False
