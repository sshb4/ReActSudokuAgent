"""A sequential model/tool loop; the controller alone establishes success."""

from copy import deepcopy
import json

from .model import Model
from .schemas import TOOL_SCHEMAS


_INSTRUCTIONS = """Solve this Sudoku. Return ONE JSON tool request per turn.
Use this workflow:
1. inspect the board. empty_cells lists row, col, candidates. Coordinates are 1-based.
2. Select a cell with ONE candidate. Before the FIRST placement, add_fact recording
   that observation with a versioned name such as Board_v0_Singleton.
3. add_rule: premises contains that fact; conclusion names its justified placement.
4. query that conclusion. When entailed, place the observed candidate in that cell.
5. inspect again. For the remaining singleton cells, place then inspect.
6. When empty_cells is empty, submit. Only validated submit establishes success.
Never place in clues or occupied cells. Every request costs one action, even
rejections. Leave an action for submit. Undo ONLY an incorrect accepted placement,
never a rejected placement or a correct forced move. Undo removes the last placement.
Facts/rules use classical propositional logic; ~ means negation. KB consistency
does not certify board truth. Board edits/undo do not retract facts: use versioned
names. Use observations and the query result, and obey rejection reasons.
"""


def run(controller, model: Model):
    state = controller.snapshot()
    if state["status"] != "running":
        return state
    messages = [{"role": "developer", "content": _INSTRUCTIONS +
                 f"\nInitial actions remaining: {state['actions_remaining']}."}]
    # Keep local status to avoid copying the entire growing trace every turn.
    status = state["status"]
    inspected = fact = rule = entailed = False
    needs_inspection = True
    empty = False
    fact_literal = conclusion = None
    while status == "running":
        if needs_inspection or not inspected:
            goal = "inspect the board to observe current empty_cells."
        elif empty:
            goal = "submit the complete board for independent validation."
        elif not fact:
            goal = "add_fact for an observed singleton. Use a positive, versioned atom naming the cell and digit. Do not negate a true observation."
        elif not rule:
            goal = ("add_rule using the EXACT accepted literal " + json.dumps(fact_literal)
                    + " as the premise, preserving its spelling and any negation. "
                    "Choose a DIFFERENT conclusion atom beginning Justified_. "
                    "Do not merely remove ~ from the fact; that would contradict it.")
        elif not entailed:
            goal = "query the EXACT rule conclusion " + json.dumps(conclusion) + " and read its entailment result."
        else:
            goal = "place a singleton candidate in its observed empty cell. Do not undo correct moves."
        prompt = deepcopy(messages)
        prompt.append({"role": "developer", "content": "NEXT GOAL: " + goal +
                       " Choose one JSON request yourself; do not repeat completed goals."})
        try:
            request = model.next_request(prompt, deepcopy(TOOL_SCHEMAS))
        except Exception:
            # Runtime errors can contain credentials or authenticated URLs.
            controller.fail_model()
            break
        observation = controller.step(request)
        if observation["ok"]:
            tool = request["tool"]
            if tool == "inspect" and request["arguments"]["scope"] == "board":
                inspected, needs_inspection = True, False
                empty = not observation["data"]["empty_cells"]
            elif tool == "add_fact":
                fact = True
                fact_literal = request["arguments"]["literal"]
            elif tool == "add_rule":
                rule = True
                conclusion = request["arguments"]["conclusion"]
            elif tool == "query" and observation["data"]["result"] == "entailed":
                entailed = True
            elif tool in ("place", "undo"):
                needs_inspection = True
        messages.append({"role": "assistant", "content": json.dumps(request)})
        messages.append({"role": "tool", "content": json.dumps(observation)})
        status = observation["status"]
    return controller.snapshot()
