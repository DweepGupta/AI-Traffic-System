import random

# ---------------- VEHICLE TYPE ---------------- #
def get_vehicle_type(cls_name):
    if cls_name == "car":
        return random.choice(["Sedan", "SUV", "Hatchback"])
    elif cls_name == "truck":
        return random.choice(["Truck (Container)", "Truck (Pickup)"])
    elif cls_name == "bus":
        return "Bus"
    elif cls_name == "motorcycle":
        return "Motorcycle"
    else:
        return cls_name


# ---------------- COLOR DETECTION ---------------- #
import numpy as np

def get_color(frame, x1, y1, x2, y2):
    h, w, _ = frame.shape

    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(w, x2)
    y2 = min(h, y2)

    roi = frame[y1:y2, x1:x2]

    if roi.size == 0:
        return "Unknown"

    avg_color = np.mean(roi, axis=(0, 1))
    b, g, r = avg_color

    if r > 150 and g < 100 and b < 100:
        return "Red"
    elif g > 150 and r < 100:
        return "Green"
    elif b > 150:
        return "Blue"
    elif r > 200 and g > 200 and b > 200:
        return "White"
    elif r < 80 and g < 80 and b < 80:
        return "Black"
    else:
        return "Grey"


# ---------------- SPEED CALCULATION ---------------- #
def calculate_speed(prev_positions, object_id, center_x, center_y):
    speed = 0

    if object_id in prev_positions:
        prev_x, prev_y = prev_positions[object_id]
        speed = abs(center_x - prev_x) + abs(center_y - prev_y)

    prev_positions[object_id] = (center_x, center_y)

    if len(prev_positions) > 100:
        prev_positions.clear()

    return speed


# ---------------- TRAFFIC DENSITY ---------------- #
def get_traffic_density(vehicle_count):
    if vehicle_count <= 3:
        return "LOW", (0, 255, 0)
    elif vehicle_count <= 7:
        return "MEDIUM", (0, 255, 255)
    else:
        return "HIGH", (0, 0, 255)


# ---------------- SIGNAL LOGIC ---------------- #
def get_signal(density):
    if density == "LOW":
        return "RED", (0, 0, 255)
    elif density == "MEDIUM":
        return "YELLOW", (0, 255, 255)
    else:
        return "GREEN", (0, 255, 0)