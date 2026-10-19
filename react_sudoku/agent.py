"""A sequential model/tool loop; the controller alone establishes success."""

from copy import deepcopy
import json

from .model import Model
from .schemas import TOOL_SCHEMAS


_INSTRUCTIONS = """Solve one 9-by-9 Sudoku using exactly one schema-constrained
tool request per turn. Coordinates and box numbers are 1-based; boxes run left
to right, top to bottom. Inspect the board to observe it. Original clues cannot
change. Place only locally legal digits in empty cells. Undo removes the latest
accepted placement. Every request, including rejected requests and inspections,
uses one action. A complete board succeeds only after an accepted submit tool.
Use observations and propositional queries when choosing placements. Facts and
rules use classical propositional logic; literals are names optionally prefixed
with ~. KB consistency does not certify board truth. Board edits and undo do not
retract KB facts: use versioned proposition names for mutable board states.
Observe rejections, recover when budget allows, and leave an action for submit.
Return only one request object matching the schema, with no explanatory text.
"""


def run(controller, model: Model):
    state = controller.snapshot()
    if state["status"] != "running":
        return state
    messages = [{"role": "developer", "content": _INSTRUCTIONS +
                 f"\nInitial actions remaining: {state['actions_remaining']}."}]
    # Keep local status to avoid copying the entire growing trace every turn.
    status = state["status"]
    while status == "running":
        try:
            request = model.next_request(deepcopy(messages), deepcopy(TOOL_SCHEMAS))
        except Exception:
            # Runtime errors can contain credentials or authenticated URLs.
            controller.fail_model()
            break
        observation = controller.step(request)
        messages.append({"role": "assistant", "content": json.dumps(request)})
        messages.append({"role": "tool", "content": json.dumps(observation)})
        status = observation["status"]
    return controller.snapshot()
