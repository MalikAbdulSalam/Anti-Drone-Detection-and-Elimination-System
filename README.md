# 🛡️ Anti-Drone (Detection and Elimination System)

This project is an **automated anti-drone system** that detects, tracks, and neutralizes aerial threats using real-time computer vision and servo motor control.  
It is equipped with a camera-mounted gun and a pan-tilt mechanism, designed to keep the target centered in the frame and activate the firing system.

## 🚀 Features

- Real-time drone detection and tracking
- Automatic pan-tilt adjustment using servo motors
- Target centering and auto-firing mechanism
- Fully autonomous operation

## 📸 Screenshot

![System Screenshot](Screenshot from 2025-05-19 12-09-03.png.png)  
*Replace `path/to/your/screenshot.png` with the actual path or URL of your screenshot image.*

---


## ⚙️ Setup Instructions

1. **Clone the repository:**

```bash
git clone https://github.com/MalikAbdulSalam/Anti-Drone-Detection-and-Elimination-System.git
cd anti-drone-system
conda env create -f environment.yaml
conda activate anti-drone
python track.py
