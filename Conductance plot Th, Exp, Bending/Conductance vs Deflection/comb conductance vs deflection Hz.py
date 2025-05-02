import cv2
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d

# === Settings ===
base_dir = "G:\\"
video_filename = "8k device 0.5bar 0.5Hz 1000ms half a cycle.h264"
resistance_file = os.path.join(base_dir, "08b1hz.xlsx")
output_excel = os.path.join(base_dir, "conductance_vs_deflection_25to30s.xlsx")
output_pdf = os.path.join(base_dir, "conductance_vs_deflection_25to30s.pdf")
VIDEO_FPS = 300

# === ROI variables ===
state = 0
p1 = p2 = p3 = p4 = None

def get_size(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 220, 255, 0)
    if abs(p3[1] - p4[1]) < abs(p3[0] - p4[0]):
        y0 = int(((p3[1] - p2[1]) + (p4[1] - p2[1])) / 2)
        x0 = int((p4[0] - p3[0]) / 2)
        row = thresh[y0]
        x1 = x2 = x0
        while x1 > 0 and row[x1] == 0: x1 -= 1
        while x2 < len(row) - 1 and row[x2] == 0: x2 += 1
        return x2 - x1
    else:
        x0 = abs(int(((p3[0] - p1[0]) + (p4[0] - p1[0])) / 2))
        y0 = abs(int((p4[1] - p3[1]) / 2))
        col = thresh[:, x0]
        y1 = y2 = y0
        while y1 > 0 and col[y1] == 0: y1 -= 1
        while y2 < len(col) - 1 and col[y2] == 0: y2 += 1
        return abs(y2 - y1)

def select_roi(video_path):
    global state, p1, p2, p3, p4
    cap = cv2.VideoCapture(video_path)
    cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)

    def mouse_callback(event, x, y, flags, userdata):
        global state, p1, p2, p3, p4
        if event == cv2.EVENT_LBUTTONUP:
            if state == 0: p1 = (x, y)
            elif state == 1: p2 = (x, y)
            elif state == 2: p3 = (x, y)
            elif state == 3: p4 = (x, y)
            state += 1
        elif event == cv2.EVENT_RBUTTONUP:
            p1 = p2 = p3 = p4 = None
            state = 0

    cv2.setMouseCallback("Frame", mouse_callback)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or state > 3: break
        cv2.imshow("Frame", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()
    return p1, p2, p3, p4

def get_deflection(video_path, fps):
    p1, p2, p3, p4 = select_roi(video_path)
    if not all([p1, p2, p3, p4]):
        print("[ERROR] ROI not set.")
        return [], []

    cap = cv2.VideoCapture(video_path)
    deflections = []
    timestamps = []

    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        crop = frame[p2[1]:p1[1]+1, p1[0]:p2[0]+1]
        d = get_size(crop)
        deflections.append(d)
        timestamps.append(frame_idx / fps)
        frame_idx += 1

    cap.release()
    return np.array(timestamps), np.array(deflections)

def smooth(y, window=51, poly=3):
    if len(y) < window:
        window = len(y) if len(y) % 2 == 1 else len(y) - 1
    return savgol_filter(y, window, poly) if len(y) >= 5 else y

def align_and_save(res_path, video_path, output_excel, output_pdf):
    # Load resistance data
    df = pd.read_excel(res_path)
    df["Time (s)"] = np.arange(0, len(df) * (1 / 11.68), 1 / 11.68)
    resistance_raw = df["Resistance (Ohm)"].values

    # Convert to conductance in mS
    conductance_mS = 1000 / resistance_raw

    # Get video deflection data
    video_time, pixel_values = get_deflection(video_path, VIDEO_FPS)
    pixel_values_smooth = smooth(pixel_values)

    # Interpolate conductance to video timestamps
    interp_conductance = interp1d(df["Time (s)"], conductance_mS, fill_value="extrapolate")
    aligned_conductance = interp_conductance(video_time)

    # Combine and export
    out_df = pd.DataFrame({
        "Time (s)": video_time,
        "Conductance (mS)": aligned_conductance,
        "Pixel Deflection (px)": pixel_values_smooth
    })

    zoom_df = out_df[(out_df["Time (s)"] >= 20) & (out_df["Time (s)"] <= 25)].copy()
    zoom_df.to_excel(output_excel, index=False)
    print(f"[SAVED] Zoomed 20–25s data exported to: {output_excel}")

    # Plot
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(zoom_df["Time (s)"], zoom_df["Conductance (mS)"], color='green', linewidth=2)
    ax1.set_xlabel("Time (s)", fontsize=12)
    ax1.set_ylabel("Conductance (mS)", color='green', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='green')

    ax2 = ax1.twinx()
    ax2.plot(zoom_df["Time (s)"], zoom_df["Pixel Deflection (px)"], color='blue', linewidth=2, linestyle='--')
    ax2.set_ylabel("Pixel Deflection (px)", color='blue', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='blue')

    plt.title("Conductance vs Pixel Deflection (20s to 25s)", fontsize=14)
    fig.tight_layout()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.savefig(output_pdf, format="pdf", bbox_inches='tight')
    plt.show()
    print(f"[SAVED] Plot exported to PDF: {output_pdf}")

# === Run ===
video_path = os.path.join(base_dir, video_filename)
align_and_save(resistance_file, video_path, output_excel, output_pdf)
