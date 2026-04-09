import os

print("🚀 Starting AI Traffic System...")

# Run detection
os.system("python -m detection.detect")

# Run dashboard
print("📊 To run dashboard:")
print("streamlit run dashboard/dashboard.py")