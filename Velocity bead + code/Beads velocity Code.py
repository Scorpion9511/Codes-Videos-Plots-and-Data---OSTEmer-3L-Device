import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# === Configuration ===
VIDEO_PATH = "G:/Beads tracking video for flow rate measurment.mp4"
OUTPUT_VIDEO_PATH = "G:/tracked_video.mp4"

# === Physical Constant ===
PIXEL_TO_UM = 0.174  # µm/pixel for 4.5X magnification

# === Open Video ===
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    raise FileNotFoundError(f"❌ Cannot open video file: {VIDEO_PATH}")

# === Video Properties ===
fps = cap.get(cv2.CAP_PROP_FPS)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# === Output Video Writer ===
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(OUTPUT_VIDEO_PATH, fourcc, fps, (frame_width, frame_height))

# === Background Subtractor ===
fgbg = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50, detectShadows=False)

# === Read First Frame ===
ret, first_frame = cap.read()
if not ret:
    raise ValueError("❌ Cannot read the first frame of the video")

prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)

# === Optical Flow Parameters ===
lk_params = dict(winSize=(15, 15), maxLevel=2,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

# === Velocity Tracking ===
velocities_um_s = []
frame_number = 0

while True:
    ret, next_frame = cap.read()
    if not ret:
        break

    next_gray = cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY)
    fgmask = fgbg.apply(next_frame)
    fgmask = cv2.medianBlur(fgmask, 5)

    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    moving_points = []

    for cnt in contours:
        if cv2.contourArea(cnt) > 10:
            x, y, w, h = cv2.boundingRect(cnt)
            moving_points.append([x + w // 2, y + h // 2])

    if len(moving_points) > 0:
        prev_points = np.array(moving_points, dtype=np.float32).reshape(-1, 1, 2)
        next_points, status, err = cv2.calcOpticalFlowPyrLK(prev_gray, next_gray, prev_points, None, **lk_params)

        good_new = next_points[status == 1]
        good_old = prev_points[status == 1]

        speed_px = np.linalg.norm(good_new - good_old, axis=1).mean()
        speed_um_s = speed_px * PIXEL_TO_UM * fps
        velocities_um_s.append(speed_um_s)

        for new, old in zip(good_new, good_old):
            a, b = new.ravel()
            c, d = old.ravel()
            cv2.line(next_frame, (int(a), int(b)), (int(c), int(d)), (0, 255, 0), 2)
            cv2.circle(next_frame, (int(a), int(b)), 5, (0, 0, 255), -1)

    out.write(next_frame)
    prev_gray = next_gray.copy()
    frame_number += 1

cap.release()
out.release()

# === Sharpest 3 Peak Detection ===
peaks, _ = find_peaks(velocities_um_s, height=0)
peak_values = [(i, velocities_um_s[i]) for i in peaks]

# Get top 3 sharpest peaks by height
top_peaks = sorted(peak_values, key=lambda x: x[1], reverse=True)[:3]
top_peak_indices = [i for i, _ in top_peaks]
top_peak_values = [v for _, v in top_peaks]

# Average of top 3
sharpest_peak_avg = np.mean(top_peak_values) if top_peak_values else 0.0

# === Plot Velocity ===
plt.figure(figsize=(10, 4))
plt.plot(velocities_um_s, label="Bead Velocity (µm/s)", color='blue')
plt.plot(peaks, [velocities_um_s[i] for i in peaks], "ro", label="Detected Peaks")
plt.plot(top_peak_indices, top_peak_values, "go", markersize=8, label="Top 3 Peaks")
plt.axhline(sharpest_peak_avg, color='red', linestyle="--",
            label=f"Top-3 Peak Avg: {sharpest_peak_avg:.2f} µm/s")
plt.xlabel("Frame")
plt.ylabel("Velocity (µm/s)")
plt.title("Bead Velocity Over Time (Top 3 Peak Average)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# === Output ===
print("\n✅ Bead Velocity Analysis Complete:")
print(f"• Top-3 Sharpest Peak Average Velocity = {sharpest_peak_avg:.2f} µm/s")
print(f"• Top 3 Peaks: {top_peak_values}")
print(f"\n🎬 Tracked video saved to: {OUTPUT_VIDEO_PATH}")
