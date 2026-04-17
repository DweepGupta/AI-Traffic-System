🚦 AI Traffic Control System

---

🔥 Overview

This project is an AI-powered smart traffic management system that:

- Detects vehicles using YOLOv8
- Uses Q-Learning (Reinforcement Learning) for signal optimization
- Dynamically adjusts traffic signals
- Handles emergency vehicles
- Displays real-time data on a live dashboard

👉 Designed to simulate a real-world intelligent traffic junction

---

⚙️ Tech Stack

- Python 🐍  
- OpenCV 👁️  
- YOLOv8 🤖  
- Reinforcement Learning (Q-Learning) 🧠  
- Streamlit 📊  
- JSON / CSV 📁  

---

🧠 Key Features

🚗 1. Vehicle Detection (YOLOv8)

- Detects:
  - Cars
  - Bikes
  - Buses
  - Trucks
  - Bicycles
- Runs on 4-direction multi-camera input

---

🧠 2. Reinforcement Learning (Q-Learning)

- Implements Q-Learning for decision making
- Learns:
  - Which signal timing reduces congestion
  - Which lane should get priority

⚙️ How it works:

- State → Traffic density per lane
- Action → Signal duration / next direction
- Reward → Reduced waiting time / congestion

📁 Q-table is stored in:

data/q_table.json

👉 Enables:

- Persistent learning across cycles
- Smarter decisions over time

---

🚦 3. Smart Traffic Signal Control

- Dynamic green light timing
- Based on:
  - AI decisions (Q-learning)
  - Vehicle density
- No fixed timers

---

⚖️ 4. Fairness System (No Starvation)

- Tracks waiting time for each direction
- Ensures:
  - No lane is ignored
  - Balanced traffic flow

---

🚑 5. Emergency Vehicle Priority

- Manual trigger (N / E / S / W)
- Instantly turns signal green
- Siren activation
- 🚨 Dashboard shows EMERGENCY mode

---

⏸️ 6. Smart Timer Handling

- Timer pauses during emergency
- Resumes from exact same point
- No time loss (real-world simulation)

---

📊 7. Live Dashboard (Streamlit)

Displays:

- Current signal
- Time left / Emergency status
- Total challans
- Analytics

---

🧾 8. Auto Challan System

- Detects violations:
  - No helmet
  - No seatbelt
  - Overspeeding
- Stores in CSV

---

🎥 9. Multi-Camera Grid

- North, East, South, West views
- 2x2 layout
- Real-time detection boxes

---

🌙 10. Robust Detection System

Handles real-world challenges:

✔ Night Conditions

- Improved visibility using frame enhancement

✔ Shadows

- Reduces false detections

✔ Occlusion

- Handles partially hidden vehicles

👉 Makes detection more reliable

---

🏗️ Project Structure (Logical Structure)

AI-Surveillance/
│
├── backend/
│   ├── signal_controller.py
│   ├── logic.py
│   ├── data_handler.py
│   ├── ai_model.py
│
├── detection/
│   ├── detect.py
│   ├── enhancer.py
│
├── dashboard/
│   ├── dashboard.py
│
├── config/
│   ├── settings.py
│
├── data/
│   ├── .gitkeep
│   ├── challans.csv
|   ├── q_table.json 
|   ├── signal.json  ← Q-table storage
│
├── models/
│   ├── yolov8n.pt
│
├── videos/
│   ├── north.mp4
│   ├── south.mp4
│   ├── east.mp4
│   ├── west.mp4
│
├── assets/
│   ├── siren.wav
│
└── main.py

---

⚙️ How It Works

🔄 Pipeline

1. Video input → YOLO detection
2. Vehicle count per direction
3. Q-learning evaluates best action
4. Signal controller updates timing
5. Dashboard updates in real-time

---

🎮 Controls

Key | Action
N |  Emergency North
E |  Emergency East
S |  Emergency South
W |  Emergency West
X |  Stop Emergency
Q |  Quit

---

🚀 How to Run

1. Install dependencies

pip install -r requirements.txt

2. Run detection

python -m detection.detect

3. Run dashboard

streamlit run dashboard/dashboard.py

---

📈 Performance

- Real-time processing
- Stable signal switching
- Smooth UI

---

🏆 Highlights

✔ Reinforcement Learning implemented
✔ Real-time AI decision making
✔ Emergency handling system
✔ Robust detection (night + occlusion + shadows)
✔ Professional dashboard

---

🔮 Future Improvements

- Multi-junction coordination
- Cloud deployment
- Advanced tracking (DeepSORT)
- Scalable architecture

---

💼 Use Cases

- Smart cities
- AI traffic systems
- Surveillance systems
- Academic projects

---

👨‍💻 Author

Dweep Gupta
B.Tech CSE

---

⭐ Final Note

This project combines:

👉 Computer Vision (YOLO)
👉 Reinforcement Learning (Q-Learning)
👉 Real-time systems

to build a next-generation smart traffic controller.

---

🔥 Built to simulate real-world intelligent infrastructure