import cv2

# Store previous counts for occlusion handling
prev_counts = {
    "north": 0,
    "east": 0,
    "south": 0,
    "west": 0
}


# 🌙 NIGHT + SHADOW FIX
def enhance_frame(frame):
    # Improve brightness (night)
    frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)

    # Remove shadows using HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    v = hsv[:, :, 2]

    _, mask = cv2.threshold(v, 60, 255, cv2.THRESH_BINARY)
    frame = cv2.bitwise_and(frame, frame, mask=mask)

    return frame


# 🚗 OCCLUSION FIX
def enhance_count(direction, current_count):
    prev = prev_counts.get(direction, 0)

    # If sudden drop → occlusion assumed
    if current_count < prev:
        current_count = int(0.7 * prev)

    prev_counts[direction] = current_count

    return current_count