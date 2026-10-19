"""Classical propositional facts/rules, checked using a small DPLL SAT solver."""

from .schemas import failure, success, valid_literal


def _negate(literal):
    return literal[1:] if literal.startswith("~") else "~" + literal


def _satisfiable(clauses):
    # A clause containing both L and ~L is a tautology.
    clauses = [clause for clause in clauses
               if not any(_negate(literal) in clause for literal in clause)]
    while True:
        if not clauses:
            return True
        if any(not clause for clause in clauses):
            return False
        unit = next((next(iter(clause)) for clause in clauses if len(clause) == 1), None)
        if unit is None:
            break
        clauses = [clause - {_negate(unit)} for clause in clauses if unit not in clause]
    literal = min(min(clauses, key=len))
    return (_satisfiable(clauses + [frozenset([literal])])
            or _satisfiable(clauses + [frozenset([_negate(literal)])]))


class KnowledgeBase:
    def __init__(self):
        self._statements = set()
        self._clauses = []
        self._atoms = set()

    def _add(self, statement, literals, clause):
        if statement in self._statements:
            return success(changed=False)
        atoms = self._atoms | {literal.removeprefix("~") for literal in literals}
        if len(atoms) > 64 or len(self._statements) >= 256:
            return failure("kb_limit", "Knowledge base exceeds its atom or statement limit.")
        if not _satisfiable(self._clauses + [clause]):
            return failure("inconsistent_kb", "Statement contradicts the accepted knowledge base.")
        self._statements.add(statement)
        self._clauses.append(clause)
        self._atoms = atoms
        return success(changed=True)

    def add_fact(self, literal):
        if not valid_literal(literal):
            return failure("invalid_literal", "Expected a propositional literal.")
        return self._add(("fact", literal), [literal], frozenset([literal]))

    def add_rule(self, premises, conclusion):
        if (not isinstance(premises, list) or not 1 <= len(premises) <= 9
                or not all(valid_literal(value) for value in premises)
                or not valid_literal(conclusion)):
            return failure("invalid_rule", "Expected one through nine premises and a literal conclusion.")
        normalized = tuple(sorted(set(premises)))
        # (P1 AND ... AND Pn) -> C becomes (~P1 OR ... OR ~Pn OR C).
        clause = frozenset([*map(_negate, normalized), conclusion])
        return self._add(("rule", normalized, conclusion), [*normalized, conclusion], clause)

    def query(self, literal):
        if not valid_literal(literal):
            return failure("invalid_literal", "Expected a propositional literal.")
        if not _satisfiable(self._clauses + [frozenset([_negate(literal)])]):
            return success(result="entailed")
        if not _satisfiable(self._clauses + [frozenset([literal])]):
            return success(result="contradicted")
        return success(result="unresolved")
