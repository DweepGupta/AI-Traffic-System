from backend.ai_model import get_state, choose_action, update_q
import time
import json
import os

# EMERGENCY MODE
emergency_mode = False
emergency_direction = None
saved_state = {}
pause_start = None
paused_duration = 0

# ---------------- YELLOW SETTINGS ---------------- #
yellow_duration = 2
is_yellow = False
yellow_start_time = 0

# ---------------- FAIRNESS ---------------- #
waiting_time = {
    "north": 0,
    "east": 0,
    "south": 0,
    "west": 0
}

directions = ["north", "east", "south", "west"]

current_index = 0
current_green = directions[current_index]

green_time = 10
start_time = time.time()

# ---------------- PRE-DECISION ---------------- #
next_direction = None
next_green_time = None
decision_made = False


# ---------------- SAVE SIGNAL STATUS ---------------- #
def save_signal_status(signal, total_time, start_time):
    os.makedirs("data", exist_ok=True)

    current_time = time.time()
    elapsed = current_time - start_time - paused_duration
    remaining = max(0, int(total_time - elapsed))

    data = {
        "current_signal": signal,
        "time_left": remaining
    }

    with open("data/signal.json", "w") as f:
        json.dump(data, f)


# ---------------- ROTATION ---------------- #
def get_next_direction():
    global current_index
    current_index = (current_index + 1) % len(directions)
    return directions[current_index]

def handle_emergency(direction):
    global emergency_mode, emergency_direction
    global saved_state, current_green, start_time, green_time

    if not emergency_mode:
        # Save current state
        saved_state = {
            "current_green": current_green,
            "start_time": start_time,
            "green_time": green_time
        }
        global pause_start
        pause_start = time.time()

    emergency_mode = True
    emergency_direction = direction

    current_green = direction
    start_time = time.time()
    green_time = 9999  # effectively infinite

def stop_emergency():
    global emergency_mode, saved_state
    global current_green, start_time, green_time

    if emergency_mode:
        emergency_mode = False

        global paused_duration, pause_start

        if pause_start is not None:
            paused_duration += time.time() - pause_start
            pause_start = None

        # Restore previous state
        current_green = saved_state["current_green"]
        start_time = saved_state["start_time"]
        green_time = saved_state["green_time"]


# ---------------- SMART DECISION ---------------- #
def decide_next_green(traffic_data):
    global waiting_time

    next_dir = get_next_direction()

    traffic = traffic_data.get(next_dir, 0)
    wait = waiting_time[next_dir]

    # Smart time calculation
    # ADAPTIVE LOGIC
    base_time = 8
    if traffic < 5:
        traffic_factor = traffic * 1.2
    elif traffic < 15:
        traffic_factor = traffic * 1.8
    else:
        traffic_factor = traffic * 2.5
    wait_factor = wait * 1.2

    default_time = base_time + (traffic * 2.5) + (wait * 1.5)

    # Clamp values
    default_time = max(8, min(int(default_time), 25))

    try:
        state = get_state(traffic_data)
        ai_time = choose_action(state)
        print("AI TIME:", ai_time)
        print("TRAFFIC:", traffic_data)

        # Blend logic + AI
        new_time = int(0.3 * default_time + 0.7 * ai_time)

    except:
        new_time = default_time

    waiting_time[next_dir] = 0

    for d in directions:
        if d != next_dir:
            waiting_time[d] += max(1, traffic_data.get(d, 0) // 3)

    return next_dir, int(new_time)


# ---------------- MAIN CONTROLLER ---------------- #
def update_signal(traffic_data):
    global current_green, green_time, start_time
    global next_direction, next_green_time, decision_made
    global is_yellow, yellow_start_time
    global emergency_mode, emergency_direction, saved_state
    global paused_duration

    current_time = time.time()
    
    # EMERGENCY HOLD MODE
    if emergency_mode:
        save_signal_status(current_green, green_time, start_time)
        return current_green, 0, "GREEN"

    # ---------------- YELLOW PHASE ---------------- #
    if is_yellow:
        elapsed_yellow = current_time - yellow_start_time

        if elapsed_yellow >= yellow_duration:
            is_yellow = False

            # SWITCH AFTER YELLOW
            if next_direction is not None:
                current_green = next_direction
                green_time = next_green_time
            else:
                current_green = get_next_direction()
                green_time = 10

            start_time = current_time
            paused_duration = 0

            # RESET DECISION
            decision_made = False
            next_direction = None
            next_green_time = None

            save_signal_status(current_green, green_time, start_time)

            return current_green, green_time, "GREEN"

        else:
            save_signal_status(current_green, yellow_duration, yellow_start_time)
            return current_green, 0, "YELLOW"

    # ---------------- NORMAL FLOW ---------------- #
    elapsed = current_time - start_time - paused_duration
    remaining = int(green_time - elapsed)

    # PRE-DECISION (5 sec before)
    if remaining <= 5 and not decision_made:
        next_direction, next_green_time = decide_next_green(traffic_data)
        decision_made = True

    # SWITCH TO YELLOW
    if remaining <= 0 and not is_yellow:
        is_yellow = True
        yellow_start_time = current_time
        return current_green, 0, "YELLOW"
    
    # AI LEARNING
    try:
        state = get_state(traffic_data)
        reward = -sum(traffic_data.values())
        update_q(state, next_green_time if next_green_time else green_time, reward)
    except:
        pass

    remaining_time = max(0, int(green_time - (time.time() - start_time - paused_duration)))

    save_signal_status(current_green, green_time, start_time)

    return current_green, remaining_time, "GREEN"