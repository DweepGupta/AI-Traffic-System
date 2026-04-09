import pandas as pd
from datetime import datetime
import os

FILE = "data/challans.csv"

# Ensure file exists
if not os.path.exists(FILE):
    df = pd.DataFrame(columns=[
        "Number Plate", "Violation", "Vehicle", "Color", "Details",
        "Time", "Date", "Status", "Due Date", "Fine"
    ])
    df.to_csv(FILE, index=False)

def add_challan(number_plate, violation, vehicle, color, details):
    now = datetime.now()

    new_entry = {
        "Number Plate": number_plate,
        "Violation": violation,
        "Vehicle": vehicle,
        "Color": color,
        "Details": details,
        "Time": now.strftime("%I:%M %p"),
        "Date": now.strftime("%Y-%m-%d"),
        "Status": "Unpaid",
        "Due Date": str(now.date()),
        "Fine": 0
    }

    df = pd.read_csv(FILE)
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_csv(FILE, index=False)