from backend.signal_controller import update_signal, handle_emergency, stop_emergency
from detection.enhancer import enhance_frame, enhance_count
from backend.data_handler import add_challan
from ultralytics import YOLO
import numpy as np
import pygame
import random
import time
import cv2

def draw_signal_panel(panel, current_green, state):
    directions = ["north", "east", "south", "west"]

    y = 80

    for d in directions:
        red = (0, 0, 255)
        green = (0, 255, 0)
        yellow = (0, 255, 255)

        if d == current_green:
            if state == "GREEN":
                color = green
            else:
                color = yellow
        else:
            color = red

        # Draw circle
        cv2.circle(panel, (60, y), 20, color, -1)

        # Label
        cv2.putText(panel, d.upper(), (100, y+5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

        # WALK logic (green for red directions)
        if d != current_green:
            cv2.putText(panel, "WALK", (200, y+5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        else:
            cv2.putText(panel, "STOP", (200, y+5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

        y += 70

from backend.logic import (
    get_vehicle_type,
    get_color,
    calculate_speed,
    get_traffic_density,
)

from config.settings import (
    CONFIDENCE_THRESHOLD,
    SPEED_THRESHOLD,
    CHALLAN_COOLDOWN,
    USE_WEBCAM,
    MODEL_PATH,
    VIDEO_PATH
)

# Load YOLO model
model = YOLO(MODEL_PATH)
model.fuse()
pygame.mixer.init()
siren_sound = pygame.mixer.Sound("assets/siren.wav")

# Webcam or Video
video_paths = {
    "north": "videos/north.mp4",
    "south": "videos/south.mp4",
    "east": "videos/east.mp4",
    "west": "videos/west.mp4"
}

cameras = {
    direction: cv2.VideoCapture(path)
    for direction, path in video_paths.items()
}

cv2.namedWindow("AI Surveillance", cv2.WINDOW_NORMAL)
cv2.resizeWindow("AI Surveillance", 1000, 700)

vehicle_classes = ["car", "motorcycle", "bus", "truck", "bicycle"]

vehicle_type_count = {
    "car": 0,
    "motorcycle": 0,
    "bus": 0,
    "truck": 0,
    "bicycle": 0
}

# tracking + cooldown
prev_positions = {}
prev_boxes = {}
last_challan_time = 0
frame_count = 0
directions = ["north", "east", "south", "west"]
current_cam_index = 0
frames = {}
siren_playing = False
emergency_mode = False
emergency_direction_global = None
# SMART MEMORY (WAIT TIME — NEW)
waiting_time = {
    "north": 0,
    "east": 0,
    "south": 0,
    "west": 0
}
while True:
    key = cv2.waitKey(1) & 0xFF

    # START EMERGENCY
    if key == ord('n'):
        emergency_mode = True
        emergency_direction_global = "north"
        if not siren_playing:
            siren_sound.play(-1)
            siren_playing = True

    elif key == ord('e'):
        emergency_mode = True
        emergency_direction_global = "east"
        if not siren_playing:
            siren_sound.play(-1)
            siren_playing = True

    elif key == ord('s'):
        emergency_mode = True
        emergency_direction_global = "south"
        if not siren_playing:
            siren_sound.play(-1)
            siren_playing = True

    elif key == ord('w'):
        emergency_mode = True
        emergency_direction_global = "west"
        if not siren_playing:
            siren_sound.play(-1)
            siren_playing = True

    # STOP EMERGENCY
    elif key == ord('x'):
        emergency_mode = False
        stop_emergency()

        siren_sound.stop()
        siren_playing = False

    # EXIT
    elif key == ord('q'):
        break

    active_direction = directions[current_cam_index]
    current_cam_index = (current_cam_index + 1) % 4
    frame_count += 1

    traffic_data = {}
    main_frame = None
    for key in vehicle_type_count:
            vehicle_type_count[key] = 0
    for direction, cap in cameras.items():

        ret, frame = cap.read()

        if frame is not None:
            frame = enhance_frame(frame)

        if not ret:
           cap.release()
           cap = cv2.VideoCapture(video_paths[direction])
           cameras[direction] = cap
           ret, frame = cap.read()

        if not ret:
           frame = frames.get(direction, np.zeros((480,640,3), dtype=np.uint8))

        if frame_count % 3 == 0:
           # Run YOLO
           results = model(frame, imgsz=320, conf=0.3, verbose=False)

           if results and results[0].boxes is not None:
              boxes = results[0].boxes
              prev_boxes[direction] = boxes
           else:
              boxes = prev_boxes.get(direction, [])
              if boxes is None:
                  boxes = []
        else:
           # Reuse previous boxes
           boxes = prev_boxes.get(direction, [])

           if boxes is None or len(boxes) == 0:
               boxes = []

        # Always store frame
        frames[direction] = frame.copy()

        vehicle_count = 0

        for box in boxes:
            cls_id = int(box.cls[0])
            cls_name = model.names[cls_id]
            confidence = float(box.conf[0])

            if cls_name in vehicle_classes and confidence > CONFIDENCE_THRESHOLD:
                vehicle_count += 1
                vehicle_type_count[cls_name] += 1

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                vehicle_type = get_vehicle_type(cls_name)
                vehicle_color = get_color(frame, x1, y1, x2, y2)

                # Draw box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

                label = f"{cls_name} {confidence:.2f}"
                (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 4)

                cv2.rectangle(frame,
                  (x1, max(0, y1 - text_h - 15)),
                  (x1 + text_w, y1),
                  (0, 0, 0),
                  -1)
                cv2.putText(frame, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 5)

                # ---------------- SPEED LOGIC ---------------- #
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)

                object_id = f"{cls_name}_{center_x//50}_{center_y//50}"
                speed = calculate_speed(prev_positions, object_id, center_x, center_y)

                # ---------------- AUTO CHALLAN LOGIC ---------------- #
                current_time = time.time()

                if (current_time - last_challan_time) > CHALLAN_COOLDOWN:

                    fake_plate = "PB" + str(random.randint(10,99)) + "XX" + str(random.randint(1000,9999))

                    # Overspeed
                    if speed > SPEED_THRESHOLD:
                        add_challan(fake_plate, "Over Speeding", vehicle_type, vehicle_color, f"{speed} speed units")
                        last_challan_time = current_time

                    # Helmet
                    if cls_name == "motorcycle" and random.random() < 0.4:
                        add_challan(fake_plate, "No Helmet", vehicle_type, vehicle_color, "-")
                        last_challan_time = current_time

                    # Seatbelt
                    if cls_name == "car" and random.random() < 0.2:
                        add_challan(fake_plate, "No Seatbelt", vehicle_type, vehicle_color, "-")
                        last_challan_time = current_time
        #  WEIGHTED TRAFFIC
        weighted_count = (
            vehicle_type_count["car"] * 1 +
            vehicle_type_count["motorcycle"] * 0.7 +
            vehicle_type_count["bus"] * 4 +
            vehicle_type_count["truck"] * 5 +
            vehicle_type_count["bicycle"] * 0.3
        )

        # AI STABILIZATION
        final_count = enhance_count(direction, weighted_count)

        traffic_data[direction] = int(final_count)
    raw_traffic_data = traffic_data.copy()
    if frame_count % 30 == 0:
        print(traffic_data)

    #  FAIRNESS BOOST
    for d in waiting_time:
        if 'current_signal' in locals():
            if d != current_signal:
                waiting_time[d] += 1
            else:
                waiting_time[d] = 0
        else:
            waiting_time[d] += 0

    # Fairness bonus
    for d in traffic_data:
        traffic_data[d] += min(waiting_time[d] * 0.6,8)

    # Convert to int
    for d in traffic_data:
        traffic_data[d] = int(traffic_data[d])
    
    # ---------------- MULTI CAMERA GRID ---------------- #

    north = frames.get("north")
    east = frames.get("east")
    south = frames.get("south")
    west = frames.get("west")

    if north is None: north = np.zeros((480,640,3), dtype=np.uint8)
    if east is None: east = np.zeros((480,640,3), dtype=np.uint8)
    if south is None: south = np.zeros((480,640,3), dtype=np.uint8)
    if west is None: west = np.zeros((480,640,3), dtype=np.uint8)

    north=cv2.resize(north,(600,400))
    east=cv2.resize(east,(600,400))
    south=cv2.resize(south,(600,400))
    west=cv2.resize(west,(600,400))

    # Add labels to each camera
    cv2.putText(north, "NORTH", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
    cv2.putText(east, "EAST", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
    cv2.putText(south, "SOUTH", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
    cv2.putText(west, "WEST", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
    # EMERGENCY DISPLAY (PER CAMERA)
    if emergency_mode and emergency_direction_global:

        if emergency_direction_global == "north":
            cv2.putText(north,
                        "EMERGENCY",
                        (200, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2,
                        cv2.LINE_AA)

        elif emergency_direction_global == "east":
            cv2.putText(east,
                        "EMERGENCY",
                        (200, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2,
                        cv2.LINE_AA)

        elif emergency_direction_global == "south":
            cv2.putText(south,
                        "EMERGENCY",
                        (200, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2,
                        cv2.LINE_AA)

        elif emergency_direction_global == "west":
            cv2.putText(west,
                        "EMERGENCY",
                        (200, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2,
                        cv2.LINE_AA)

    # Combine frames
    top = cv2.hconcat([north, east])
    bottom = cv2.hconcat([south, west])

    grid = cv2.vconcat([top, bottom])
    h, w, _ = grid.shape
    panel_width = int(w * 0.20)
    grid_width = w - panel_width

    grid = cv2.resize(grid, (grid_width, h))

    panel = np.zeros((h, panel_width, 3), dtype=np.uint8)

    main_frame = cv2.hconcat([panel, grid])

    # ---------------- TRAFFIC LOGIC ---------------- #
    total_vehicles = int(sum(raw_traffic_data.values()))
    density, color = get_traffic_density(total_vehicles)

    # Signal logic
    if emergency_mode and emergency_direction_global is not None:
        handle_emergency(emergency_direction_global)
    
    current_signal, remaining_time, phase = update_signal(traffic_data)
    display_time = remaining_time + (2 if phase == "GREEN" else 0)

    panel[:] = (25, 25, 25)

    # ---------------- DISPLAY ---------------- #
    # Background box
    h, w, _ = main_frame.shape

    panel_width = int(w * 0.20)

    # Left panel

    font = cv2.FONT_HERSHEY_SIMPLEX

    x = 10
    y = 50

    # Title
    text = "AI TRAFFIC"
    (text_w, _), _ = cv2.getTextSize(text, font, 0.8, 2)

    x_center = (panel_width - text_w) // 2

    cv2.putText(main_frame[:, :panel_width], text,
           (x_center, y),
           font, 0.8, (255,255,255), 2, cv2.LINE_AA)
    y += 65

    # Vehicles
    cv2.putText(main_frame[:, :panel_width], f"Veh: {total_vehicles}", (x, y),
                font, 0.8, (200, 200, 200), 2,cv2.LINE_AA)
    y += 40

    # Traffic
    cv2.putText(main_frame[:, :panel_width], f"{density}", (x, y),
                font, 0.8, color, 2,cv2.LINE_AA)
    y += 40

    # Signal
    if current_signal == "PEDESTRIAN":
        cv2.putText(main_frame[:, :panel_width], "WALK", (x, y),
                    font, 0.8, (0, 255, 255), 3)
    else:
        cv2.putText(main_frame[:, :panel_width], f"{current_signal}", (x, y),
                    font, 0.8, (0, 255, 0), 3)

    y += 40

    # Time
    cv2.putText(main_frame[:, :panel_width], f"{int(round(remaining_time))}s", (x, y),
                font, 0.8, (255, 255, 255), 2,cv2.LINE_AA)

    y += 50

    # Divider
    cv2.line(main_frame[:, :panel_width], (5, y), (panel_width - 5, y), (80, 80, 80), 1)
    y += 75

    # ---------------- NEW SIGNAL UI ---------------- #
    dirs = ["north", "east", "south", "west"]

    for i, d in enumerate(dirs):
        y_pos = y + i * 55

        # Direction (LEFT)
        cv2.putText(main_frame[:, :panel_width], d.upper(),
                (10, y_pos),
                font, 0.6, (255,255,255), 2, cv2.LINE_AA)

        if d == current_signal:
            # 🟢 GREEN / 🟡 YELLOW
            if phase == "GREEN":
                signal_color = (0,255,0)
                status = "GO"
            else:
                signal_color = (0,255,255)
                status = "GO"

            # Circle
            cv2.circle(main_frame[:, :panel_width],
                   (panel_width - 60, y_pos - 10),
                   10, signal_color, -1)

            # Status
            cv2.putText(main_frame[:, :panel_width], status,
                    (panel_width - 45, y_pos),
                    font, 0.6, (0,255,0), 2, cv2.LINE_AA)

        else:
            # 🔴 RED
            signal_color = (0,0,255)

            # WALK
            cv2.putText(main_frame[:, :panel_width], "WALK",
                    (85, y_pos),
                    font, 0.6, (0,255,0), 2, cv2.LINE_AA)

            # Circle
            cv2.circle(main_frame[:, :panel_width],
                   (panel_width - 60, y_pos - 10),
                   10, signal_color, -1)

            # Timer
            # Proper red countdown
            green_remaining = max(0, int(round(remaining_time)))

            yellow_time = 2

            cycle_time = green_remaining + yellow_time

            if cycle_time < 0:
                cycle_time = 0

            # POSITION DIFFERENCE
            current_index = dirs.index(current_signal)
            this_index = dirs.index(d)

            diff = (this_index - current_index) % 4

            if diff == 1:
                if cycle_time > 0:
                    status = f"{cycle_time}s"  # NEXT TURN
                else:
                    status = "0s"
            else:
                status = "WAIT"  # FUTURE TURNS
            cv2.putText(main_frame[:, :panel_width], status,
                    (panel_width - 45, y_pos),
                    font, 0.6, (255,255,255), 2, cv2.LINE_AA)
    cv2.imshow("AI Surveillance", main_frame)

for cap in cameras.values():
    cap.release()
cv2.destroyAllWindows()