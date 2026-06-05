# 🚗 AI-Based Driver Monitoring System  
![Status](https://img.shields.io/badge/Project-Active-brightgreen?style=for-the-badge)
![AI](https://img.shields.io/badge/AI_Computer_Vision-Advanced-blueviolet?style=for-the-badge)
![Embedded](https://img.shields.io/badge/Embedded_System-Arduino-orange?style=for-the-badge)

This project is a complete AI-powered driver safety solution that monitors the driver’s face and behavior in real time. It detects drowsiness, distraction, phone usage, yawning, blinking, and head tilt using MediaPipe, YOLOv8, and an Arduino-based alert module. The system provides instant warnings to reduce accidents caused by fatigue or inattention.

---
## 🎥 Demo Video

<video src="https://github.com/NagendraKumarMuliki/AI-Based-Driver-Monitoring-System/raw/main/images/AI-Based-Driver-Monitoring-System-DEMO.mp4" 
       controls 
       width="700">
</video>

---
## 🔧 Technologies Used  

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe_Face_Mesh-00C853?style=for-the-badge&logo=google&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8_Object_Detection-7E57C2?style=for-the-badge&logo=opencv&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-CV2-FF6F00?style=for-the-badge&logo=opencv&logoColor=white)
![Arduino](https://img.shields.io/badge/Arduino_Uno-00979D?style=for-the-badge&logo=arduino&logoColor=white)
![Bluetooth](https://img.shields.io/badge/HC--05_Bluetooth-1E88E5?style=for-the-badge&logo=bluetooth&logoColor=white)
![LEDMatrix](https://img.shields.io/badge/HT16K33_LED_Matrix-795548?style=for-the-badge)
![PySerial](https://img.shields.io/badge/PySerial-000000?style=for-the-badge)
![EmbeddedC](https://img.shields.io/badge/Embedded_C-FFFFFF?style=for-the-badge&logo=c&logoColor=000)

---

## 🔍 System Overview  

The system operates in two coordinated layers.

The **AI Vision Module** (Python) captures the webcam feed, extracts facial landmarks, detects phone usage, and classifies the driver’s current state using MediaPipe and YOLOv8.

The **Hardware Alert Module** (Arduino) receives a state code via Bluetooth and activates LEDs, buzzer patterns, and LED matrix icons to warn the driver.

Both modules run continuously to ensure uninterrupted monitoring and instant alerts.

---

## 🧠 AI Detection Logic (Deep Explanation)

### **Drowsiness Detection**  
Uses the Eye Aspect Ratio (EAR). When eyes remain closed for a sustained duration, the system marks **DROWSY**.  
A continuous buzzer sound is triggered with no pause.

### **Blink Detection**  
Short eye closures are treated as normal blinks.  
Marked as **BLINK**, no buzzer.

### **Yawn Detection**  
Uses Mouth Aspect Ratio (MAR).  
If the mouth stays open beyond a threshold → **YAWN**.  
No buzzer.

### **Distraction Detection**  
Uses head yaw angle.  
If the driver looks too far left or right → **DISTRACTED**.  
Triggers a beep–pause–beep pattern.

### **Phone Usage Detection (YOLOv8)**  
YOLOv8 detects if a phone is near the driver’s face.  
If detected → **PHONE USAGE**.  
Triggers a beep–beep–pause pattern.

### **Head Tilt Detection**  
Uses roll angle.  
If head tilts too much → **TILT**.  
No buzzer.

### **Active State**  
Normal driving condition.  
Only the Active LED glows.

---

## 🔊 Buzzer Warning Patterns  

**Drowsy:** Continuous beep (highest priority)  
**Phone Usage:** Beep–beep–pause repeating  
**Distraction:** Beep–pause–beep–pause repeating  
**Yawn:** Silent  
**Blink:** Silent  
**Tilt:** Silent  
**Active:** Silent  

The system always prioritizes the most dangerous condition.

---

## 💡 LED Indicators  

Each LED corresponds to one driver state.  
Only one LED glows at a time.  
Provides quick visual feedback even without audio alerts.

---

## 🎭 LED Matrix Icons  

🙂 Active  
😴 Drowsy  
😮 Yawn  
👀 Blink  
📵 Phone Usage  
⬅️➡️ Distraction  

These icons make the system intuitive and easy to interpret.

---

# 📡 Bluetooth Logging (Using Serial Bluetooth Terminal App)

![Bluetooth Logging](https://img.shields.io/badge/Bluetooth_Logging-Enabled-2962FF?style=for-the-badge&logo=bluetooth&logoColor=white)

The system supports **real-time Bluetooth logging** using the **Serial Bluetooth Terminal** app from the Google Play Store.

### **How Logging Works**

The Arduino sends a log message every time the driver’s state changes.  
Python sends a single character (A, B, D, Y, T, P) to Arduino, and Arduino converts it into a readable log.

### **App Used for Logging**
You can view all logs using:

📱 **Serial Bluetooth Terminal** (Play Store)  
Package: `de.kai_morich.serial_bluetooth_terminal`

This app connects to the HC‑05 module and displays all incoming logs in real time.

### **What Gets Logged**
Every state change is logged, including:

- ACTIVE  
- BLINK  
- DROWSY  
- YAWN  
- DISTRACTED  
- PHONE USAGE  
- HEAD TILT  

### **How to Connect**
1. Turn on your HC‑05 module  
2. Open **Serial Bluetooth Terminal**  
3. Tap **Connect** → choose **HC‑05**  
4. Logs will start appearing instantly  

### **Why Logging Is Useful**
- Helps analyze driver behavior  
- Useful for debugging  
- Shows how often alerts are triggered  
- Helps tune thresholds  
- Works wirelessly without USB  

---

## 🔌 Hardware Operation  

The Arduino receives a single character from Python via Bluetooth.  
Based on this code, it activates the correct LED, buzzer pattern, and LED matrix icon.  
The reset button prints a session summary through the serial monitor.

---

## ▶️ How the System Works  

1. Webcam captures the driver’s face  
2. MediaPipe extracts eye, mouth, and head pose landmarks  
3. YOLOv8 checks for phone usage  
4. Python determines the driver’s state  
5. A state code is sent to Arduino via Bluetooth  
6. Arduino activates LEDs, buzzer, and matrix icons  
7. Reset button prints a session summary  

---

## ⚠️ Disclaimer
This project is for educational and experimental use only. It is not a certified safety device and should not be relied on as the primary method for preventing accidents. Use it responsibly and at your own risk.

---

## 🙌 Acknowledgments  

Thanks to everyone who supported this project. 
