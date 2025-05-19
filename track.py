import tkinter as tk
import math
import cv2
from ultralytics import YOLO
from PIL import Image, ImageTk
import pygame

# Window size and center
WIDTH, HEIGHT = 1000, 1000
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2

FOV = 500

# Turret dimensions
BASE_RADIUS = 30
PAN_ARM_LENGTH = 200
PAN_ARM_WIDTH = 20
TILT_ARM_LENGTH = 120
TILT_ARM_WIDTH = 15

# Initial turret angles
pan_angle = 0
tilt_angle = 0
fire_flash_id = None

# Rotation functions
def rotate_x(p, angle_deg):
    angle = math.radians(angle_deg)
    x, y, z = p
    return (x, y * math.cos(angle) - z * math.sin(angle),
            y * math.sin(angle) + z * math.cos(angle))

def rotate_y(p, angle_deg):
    angle = math.radians(angle_deg)
    x, y, z = p
    return (x * math.cos(angle) + z * math.sin(angle),
            y,
            -x * math.sin(angle) + z * math.cos(angle))

def rotate_z(p, angle_deg):
    angle = math.radians(angle_deg)
    x, y, z = p
    return (x * math.cos(angle) - y * math.sin(angle),
            x * math.sin(angle) + y * math.cos(angle),
            z)

# Projection function (3D to 2D)
def project(p):
    x, y, z = p
    factor = FOV / (FOV + z) if (FOV + z) != 0 else 1
    return CENTER_X + x * factor, CENTER_Y - y * factor

# Create cuboid vertices
def create_cuboid(length, width, height):
    w = width / 2
    h = height / 2
    return [
        (0, -w, -h), (0, w, -h), (0, w, h), (0, -w, h),
        (length, -w, -h), (length, w, -h), (length, w, h), (length, -w, h)
    ]

# Draw cuboid faces on canvas
def draw_cuboid(points, color):
    faces = [
        (0, 1, 2, 3), (4, 5, 6, 7),
        (0, 4, 7, 3), (1, 5, 6, 2),
        (3, 2, 6, 7), (0, 1, 5, 4),
    ]
    # Painter's algorithm: sort faces by avg Z descending
    faces.sort(key=lambda f: sum(points[i][2] for i in f) / 4, reverse=True)
    for f in faces:
        coords = [project(points[i]) for i in f]
        flat = [v for pt in coords for v in pt]
        canvas.create_polygon(flat, fill=color, outline="black")

# Draw the turret
def draw_turret(pan, tilt):
    canvas.delete("all")
    # Base
    canvas.create_oval(CENTER_X - BASE_RADIUS, CENTER_Y - BASE_RADIUS,
                       CENTER_X + BASE_RADIUS, CENTER_Y + BASE_RADIUS,
                       fill="gray")

    # Pan arm
    pan_cuboid = create_cuboid(PAN_ARM_LENGTH, PAN_ARM_WIDTH, PAN_ARM_WIDTH)
    pan_rotated = [rotate_y(p, pan) for p in pan_cuboid]
    draw_cuboid(pan_rotated, "blue")

    tip = rotate_y((PAN_ARM_LENGTH, 0, 0), pan)

    # Tilt arm
    tilt_cuboid = create_cuboid(TILT_ARM_LENGTH, TILT_ARM_WIDTH, TILT_ARM_WIDTH)
    tilt_rotated = [rotate_z(p, tilt) for p in tilt_cuboid]
    tilt_translated = [(p[0] + PAN_ARM_LENGTH, p[1], p[2]) for p in tilt_rotated]
    tilt_world = [rotate_y(p, pan) for p in tilt_translated]
    draw_cuboid(tilt_world, "red")

    # Joint circle
    joint_x, joint_y = project(tip)
    canvas.create_oval(joint_x - 6, joint_y - 6, joint_x + 6, joint_y + 6, fill="black")

    # Display angles
    canvas.create_text(10, 10, anchor="nw", text=f"Pan: {pan}°\nTilt: {tilt}°",
                       font=("Arial", 14), fill="black")

# Initialize pygame for sound
pygame.mixer.init()
machine_gun_sound = pygame.mixer.Sound("utilts/machin_gun.mp3")

# Simulate firing flash at turret tip
def simulate_fire(pan, tilt):
    global fire_flash_id
    tip_local = (TILT_ARM_LENGTH, 0, 0)
    tip_rotated = rotate_z(tip_local, tilt)
    tip_translated = (tip_rotated[0] + PAN_ARM_LENGTH, tip_rotated[1], tip_rotated[2])
    tip_world = rotate_y(tip_translated, pan)
    tip_x, tip_y = project(tip_world)

    radius = 15
    fire_flash_id = canvas.create_oval(tip_x - radius, tip_y - radius,
                                       tip_x + radius, tip_y + radius,
                                       fill="orange", outline="red", width=2)

    def remove_flash():
        global fire_flash_id
        if fire_flash_id:
            canvas.delete(fire_flash_id)
            fire_flash_id = None

    canvas.after(150, remove_flash)

# Keyboard controls for turret
def on_key(event):
    global pan_angle, tilt_angle
    if event.keysym == "Left":
        pan_angle = (pan_angle - 5) % 360
    elif event.keysym == "Right":
        pan_angle = (pan_angle + 5) % 360
    elif event.keysym == "Up":
        tilt_angle = min(tilt_angle + 5, 90)
    elif event.keysym == "Down":
        tilt_angle = max(tilt_angle - 5, -90)

    draw_turret(pan_angle, tilt_angle)

    if event.char.lower() == "f":
        simulate_fire(pan_angle, tilt_angle)
        machine_gun_sound.play()

# Initialize webcam and YOLO model
cap = cv2.VideoCapture(0)
model = YOLO('models/drone.pt')  # Ensure this path is correct

# Setup main window
root = tk.Tk()
root.title("3D Turret Simulation")

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="white")
canvas.pack(side=tk.LEFT)

video_label = tk.Label(root)
video_label.pack(side=tk.RIGHT)

# Class names list (update as per your model)
class_names = ['drone']

# Main update loop for video & turret control
def update_turret_with_detection():
    global pan_angle, tilt_angle

    ret, frame = cap.read()
    if not ret:
        root.after(30, update_turret_with_detection)
        return

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_h, frame_w = frame.shape[:2]
    center_x, center_y = frame_w // 2, frame_h // 2
    # Draw center circle on video frame (for aiming reference)
    cv2.circle(frame_rgb, (center_x, center_y), 10, (255, 0, 0), 2)  # Blue circle with thickness 2

    results = model(frame)[0]

    target_box = None
    for box in results.boxes:
        cls_id = int(box.cls)
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
        label = class_names[cls_id] if cls_id < len(class_names) else f"class {cls_id}"

        # Draw bounding box on frame
        cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Draw label background
        (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(frame_rgb, (x1, y1 - text_height - 10), (x1 + text_width, y1), (0, 255, 0), -1)

        # Put label text
        cv2.putText(frame_rgb, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        if cls_id == 0:  # Track only class 0 ('drone')
            target_box = box
            break

    if target_box is not None:
        x1, y1, x2, y2 = target_box.xyxy[0].cpu().numpy()
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        error_x = cx - center_x
        error_y = cy - center_y
        threshold = 20

        if error_x > threshold:
            pan_angle = (pan_angle + 2) % 360
        elif error_x < -threshold:
            pan_angle = (pan_angle - 2) % 360

        if error_y > threshold:
            tilt_angle = max(tilt_angle - 2, -90)
        elif error_y < -threshold:
            tilt_angle = min(tilt_angle + 2, 90)

        # Fire if turret is aligned
        if abs(error_x) <= threshold and abs(error_y) <= threshold:
            simulate_fire(pan_angle, tilt_angle)
            machine_gun_sound.play()

        # Draw target circle
        cv2.circle(frame_rgb, (cx, cy), 40, (0, 0, 255), 3)

    # Show frame in Tkinter
    img = Image.fromarray(frame_rgb)
    imgtk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)

    draw_turret(pan_angle, tilt_angle)
    root.after(30, update_turret_with_detection)

# Bind keys and start
root.bind("<Key>", on_key)
draw_turret(pan_angle, tilt_angle)
update_turret_with_detection()
root.mainloop()
cap.release()
