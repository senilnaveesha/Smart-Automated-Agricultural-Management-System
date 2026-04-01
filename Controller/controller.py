import pygame
import socket
import time

# ================= CONFIG =================
ESP32_IP = "192.168.1.100"   # 🔥 CHANGE THIS
PORT = 14550

SEND_RATE = 50  # Hz

# =========================================

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

pygame.init()
screen = pygame.display.set_mode((500, 300))
pygame.display.set_caption("ESP32 Drone Controller")

font = pygame.font.Font(None, 36)
clock = pygame.time.Clock()

# RC values
roll = 1500
pitch = 1500
yaw = 1500
throttle = 1000

last_print = 0


def send():
    global last_print
    msg = f"{roll},{pitch},{yaw},{throttle},1000,1000,1000,1000"
    sock.sendto(msg.encode(), (ESP32_IP, PORT))

    # Print only 2 times per second (no spam)
    if time.time() - last_print > 0.5:
        print(msg)
        last_print = time.time()


def draw_ui():
    screen.fill((0, 0, 0))

    texts = [
        f"Throttle: {throttle}",
        f"Roll: {roll}",
        f"Pitch: {pitch}",
        f"Yaw: {yaw}",
        "",
        "Controls:",
        "W/S = Pitch | A/D = Roll",
        "Q/E = Yaw | Arrow Up/Down = Throttle"
    ]

    y = 20
    for t in texts:
        text_surface = font.render(t, True, (0, 255, 0))
        screen.blit(text_surface, (20, y))
        y += 30

    pygame.display.flip()


running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # Reset center
    roll = 1500
    pitch = 1500
    yaw = 1500

    # Movement
    if keys[pygame.K_w]:
        pitch = 1700
    if keys[pygame.K_s]:
        pitch = 1300
    if keys[pygame.K_a]:
        roll = 1300
    if keys[pygame.K_d]:
        roll = 1700

    # Yaw
    if keys[pygame.K_q]:
        yaw = 1300
    if keys[pygame.K_e]:
        yaw = 1700

    # Throttle (smooth)
    if keys[pygame.K_UP]:
        throttle += 5
    if keys[pygame.K_DOWN]:
        throttle -= 5

    throttle = max(1000, min(2000, throttle))

    # Send data
    send()

    # Draw UI
    draw_ui()

    clock.tick(SEND_RATE)

pygame.quit()