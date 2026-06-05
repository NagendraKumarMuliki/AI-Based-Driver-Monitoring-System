import cv2
import numpy as np
import time
from ultralytics import YOLO
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import serial

# =============== SERIAL PORT ===============
arduino = serial.Serial('COM6', 9600)
time.sleep(2)

# =============== MEDIAPIPE TASKS FACE LANDMARKER ===============
model_path = "face_landmarker.task"

BaseOptions = python.BaseOptions
FaceLandmarker = vision.FaceLandmarker
FaceLandmarkerOptions = vision.FaceLandmarkerOptions
VisionRunningMode = vision.RunningMode

options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.VIDEO,
    num_faces=1
)

detector = FaceLandmarker.create_from_options(options)

mp_face_mesh = mp.solutions.face_mesh

# =============== YOLO (PHONE DETECTION) ===============
phone_model = YOLO("yolov8n.pt")

# =============== CONSTANTS ===============
EAR_THRESH = 0.21
DROWSY_TIME = 2.0
MAR_THRESH = 0.6

DISTRACTION_YAW = 25      # UPDATED: ±25° distraction threshold
TILT_ROLL = 15

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
LEFT_IRIS = [468, 469, 470, 471]
RIGHT_IRIS = [473, 474, 475, 476]

POSE_LANDMARKS = {
    "nose": 1,
    "chin": 152,
    "left_eye": 33,
    "right_eye": 263,
    "left_mouth": 61,
    "right_mouth": 291
}

model_points = np.array([
    (0.0, 0.0, 0.0),
    (0.0, -63.6, -12.5),
    (-43.3, 32.7, -26.0),
    (43.3, 32.7, -26.0),
    (-28.9, -28.9, -24.1),
    (28.9, -28.9, -24.1)
], dtype=np.float64)

closed_start = None
smooth_yaw = 0.0
smooth_roll = 0.0
alpha = 0.2

# =============== HELPERS ===============
def EAR(lm, idx):
    p = np.array([[lm[i].x, lm[i].y] for i in idx])
    A = np.linalg.norm(p[1] - p[5])
    B = np.linalg.norm(p[2] - p[4])
    C = np.linalg.norm(p[0] - p[3])
    return (A + B) / (2.0 * C + 1e-6)

def MAR(lm):
    p13 = np.array([lm[13].x, lm[13].y])
    p14 = np.array([lm[14].x, lm[14].y])
    p78 = np.array([lm[78].x, lm[78].y])
    p308 = np.array([lm[308].x, lm[308].y])
    A = np.linalg.norm(p13 - p14)
    C = np.linalg.norm(p78 - p308)
    return A / (C + 1e-6)

def head_pose(lm, w, h):
    pts = np.array([
        (lm[1].x * w, lm[1].y * h),
        (lm[152].x * w, lm[152].y * h),
        (lm[33].x * w, lm[33].y * h),
        (lm[263].x * w, lm[263].y * h),
        (lm[61].x * w, lm[61].y * h),
        (lm[291].x * w, lm[291].y * h),
    ], dtype=np.float64)

    focal_length = w
    center = (w / 2, h / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype=np.float64)

    dist_coeffs = np.zeros((4, 1))

    success, rvec, tvec = cv2.solvePnP(
        model_points, pts, camera_matrix, dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE
    )

    if not success:
        return 0, 0, 0

    R, _ = cv2.Rodrigues(rvec)
    sy = np.sqrt(R[0, 0]**2 + R[1, 0]**2)

    pitch = np.degrees(np.arctan2(R[2, 1], R[2, 2]))
    yaw   = np.degrees(np.arctan2(-R[2, 0], sy))
    roll  = np.degrees(np.arctan2(R[1, 0], R[0, 0]))
    return pitch, yaw, roll

def draw_facemesh_tesselation(frame, lm):
    h, w, _ = frame.shape
    for conn in mp_face_mesh.FACEMESH_TESSELATION:
        i, j = conn
        x1, y1 = int(lm[i].x * w), int(lm[i].y * h)
        x2, y2 = int(lm[j].x * w), int(lm[j].y * h)
        cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)

def draw_eye_oval(frame, lm, idx, color):
    h, w, _ = frame.shape
    xs = [int(lm[i].x * w) for i in idx]
    ys = [int(lm[i].y * h) for i in idx]
    x1, y1 = min(xs), min(ys)
    x2, y2 = max(xs), max(ys)
    cx, cy = (x1 + x2)//2, (y1 + y2)//2
    ax, ay = (x2 - x1)//2, (y2 - y1)//2
    cv2.ellipse(frame, (cx, cy), (ax, ay), 0, 0, 360, color, 2)

def draw_iris(frame, lm, idx, color):
    h, w, _ = frame.shape
    pts = np.array([[lm[i].x * w, lm[i].y * h] for i in idx])
    cx, cy = int(np.mean(pts[:, 0])), int(np.mean(pts[:, 1]))
    r = int(max(np.linalg.norm(pts - np.array([cx, cy])), 2))
    cv2.circle(frame, (cx, cy), r, color, 1)

def state_label_from_command(cmd):
    return {
        "A": "ACTIVE",
        "C": "BLINK",
        "D": "DROWSY",
        "Y": "YAWNING",
        "T": "DISTRACTED",
        "P": "PHONE USAGE"
    }.get(cmd, "UNKNOWN")

# =============== CAMERA LOOP ===============
cam = cv2.VideoCapture(0)
timestamp = 0

while True:
    ret, frame = cam.read()
    if not ret:
        continue

    frame = cv2.flip(frame, 1)
    raw_frame = frame.copy()
    h, w, _ = frame.shape

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    timestamp += 1
    result = detector.detect_for_video(mp_image, timestamp)

    # ================= NO FACE DETECTED =================
    if not result.face_landmarks:
        no_face_text = "NO FACE DETECTED"
        text_size = cv2.getTextSize(no_face_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
        text_x = (w - text_size[0]) // 2
        text_y = (h + text_size[1]) // 2

        cv2.putText(frame, no_face_text, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

        arduino.write("A".encode())

        cv2.imshow("Driver Monitor AI", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    # ================= FACE DETECTED =================
    lm = result.face_landmarks[0]
    command = "A"
    countdown_text = ""

    # Mesh
    draw_facemesh_tesselation(frame, lm)

    # EAR / MAR / HEAD POSE
    ear = (EAR(lm, LEFT_EYE) + EAR(lm, RIGHT_EYE)) / 2
    mar = MAR(lm)
    pitch, yaw, roll = head_pose(lm, w, h)

    # Smooth yaw & roll
    smooth_yaw = smooth_yaw * (1 - alpha) + yaw * alpha
    smooth_roll = smooth_roll * (1 - alpha) + roll * alpha

    # Eye color
    eye_color = (0, 255, 255) if ear >= EAR_THRESH else (0, 0, 255)
    draw_eye_oval(frame, lm, LEFT_EYE, eye_color)
    draw_eye_oval(frame, lm, RIGHT_EYE, eye_color)

    draw_iris(frame, lm, LEFT_IRIS, (0, 255, 0))
    draw_iris(frame, lm, RIGHT_IRIS, (0, 255, 0))

    # Blink / Drowsy
    if ear < EAR_THRESH:
        if closed_start is None:
            closed_start = time.time()
        elapsed = time.time() - closed_start
        remaining = max(0.0, DROWSY_TIME - elapsed)

        if elapsed < DROWSY_TIME:
            command = "C"
            countdown_text = f"Drowsy in: {remaining:.1f}s"
        else:
            command = "D"
            countdown_text = "DROWSY!"
    else:
        closed_start = None

    # Yawn
    if mar > MAR_THRESH:
        command = "Y"

    # ------------------ DISTRACTION (Yaw ±25°) ------------------
    distract_label = ""
    if smooth_yaw > DISTRACTION_YAW:
        distract_label = "DISTRACTION RIGHT"
        command = "T"
    elif smooth_yaw < -DISTRACTION_YAW:
        distract_label = "DISTRACTION LEFT"
        command = "T"

    # ------------------ TILT (Roll) ------------------
    tilt_label = ""
    if smooth_roll > TILT_ROLL:
        tilt_label = "TILT RIGHT"
    elif smooth_roll < -TILT_ROLL:
        tilt_label = "TILT LEFT"

    # ------------------ YAW COLOR (updated for ±25°) ------------------
    if abs(smooth_yaw) < 10:
        yaw_color = (0, 255, 0)
    elif abs(smooth_yaw) < 25:
        yaw_color = (0, 165, 255)
    else:
        yaw_color = (0, 0, 255)

    # ------------------ FACE BOUNDING BOX ------------------
    xs = [int(p.x * w) for p in lm]
    ys = [int(p.y * h) for p in lm]
    face_left, face_right = min(xs), max(xs)
    face_top, face_bottom = min(ys), max(ys)
    face_center_y = (face_top + face_bottom) // 2

    # ------------------ SHOW YAW TEXT ------------------
    yaw_text = f"{smooth_yaw:.1f}°"

    if smooth_yaw > 10:
        cv2.putText(frame, yaw_text, (face_right + 5, face_center_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, yaw_color, 2)
    elif smooth_yaw < -10:
        cv2.putText(frame, yaw_text, (face_left - 60, face_center_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, yaw_color, 2)

    # ------------------ SHOW DISTRACTION LABEL ------------------
    if distract_label != "":
        cv2.putText(frame, distract_label, (face_left, face_top - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # ------------------ SHOW TILT LABEL ------------------
    if tilt_label != "":
        cv2.putText(frame, tilt_label, (face_left, face_top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Phone detection
    yolo = phone_model(frame, imgsz=320, verbose=False)
    for r in yolo:
        for box in r.boxes:
            if int(box.cls[0]) == 67:
                command = "P"
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2),
                              (0, 0, 255), 2)
                cv2.putText(frame, "PHONE", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (0, 0, 255), 2)

    # Send to Arduino
    arduino.write(command.encode())

    # State label (small)
    state_label = state_label_from_command(command)
    print("STATE:", state_label)

    cv2.putText(frame, state_label, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    # Countdown
    if countdown_text:
        cv2.putText(frame, countdown_text, (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Small real video window
    thumb = cv2.resize(raw_frame, (int(w * 0.25), int(h * 0.25)))
    frame[h - thumb.shape[0] - 10:h - 10,
          w - thumb.shape[1] - 10:w - 10] = thumb

    cv2.imshow("Driver Monitor AI", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
arduino.close()
cv2.destroyAllWindows()
