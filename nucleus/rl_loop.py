
import random
from typing import Any, List

class ReinforcementLoop:
    """
    Handles action selection and reward-based learning in an iterative fashion.
    """
    def __init__(self, actions: List[str] = None):
        self.actions = actions or []
        self.state = None
        self.q_table = {}

    def select_action(self, state: str, epsilon: float = 0.2) -> str:
        """
        Select an action using epsilon-greedy policy (no recursion).
        """
        if random.random() < epsilon or state not in self.q_table:
            return random.choice(self.actions) if self.actions else None
        return max(self.q_table[state], key=self.q_table[state].get)

    def update(self, state: str, new_state: str, reward: float, action: str):
        """
        Update Q-table iteratively after an action is taken.
        """
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.actions}
        if action not in self.q_table[state]:
            self.q_table[state][action] = 0.0
        self.q_table[state][action] += reward
        self.state = new_state

class Evaluator:
    """
    Evaluator agent that scores subtask results according to multiple criteria.
    Author: 
    """
    def __init__(self):
        pass

    def evaluate(self, result, expected=None):
        """
        Evaluate subtask result.
        :param result: actual result
        :param expected: expected result (optional)
        :return: score (reward, int/float)
        """
        # Simple binary evaluation (success/failure)
        if expected is not None:
            return 1.0 if result == expected else -1.0
        # If result is not empty — treat as success
        return 1.0 if result else 0.0