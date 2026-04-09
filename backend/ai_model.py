import random
import json
import os

Q_FILE = "data/q_table.json"

# LOAD Q TABLE (if exists)
if os.path.exists(Q_FILE):
    with open(Q_FILE, "r") as f:
        Q = json.load(f)
else:
    Q = {}

ACTIONS = [10, 15, 20, 25]
LR = 0.1

def get_state(traffic_data):
    return str(tuple(traffic_data.values()))

def choose_action(state):
    state = str(state)

    if state not in Q:
        Q[state] = {str(a): 0 for a in ACTIONS}

    # 🔥 30% exploration
    if random.random() < 0.3:
        return random.choice(ACTIONS)

    return int(max(Q[state], key=Q[state].get))

def update_q(state, action, reward):
    state = str(state)

    if state not in Q:
        Q[state] = {str(a): 0 for a in ACTIONS}
    action = str(action)
    Q[state][action] += LR * (reward - Q[state][action])
    # SAVE Q TABLE
    os.makedirs("data", exist_ok=True)
    with open(Q_FILE, "w") as f:
        json.dump(Q, f)