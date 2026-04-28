import time

from backend.drone_comm.udp_sender import UDPSender
from backend.drone_comm.drone_protocol import (
    make_path_start,
    make_path_point,
    make_path_end,
    make_start_scan,
    make_stop_scan,
    make_manual_control,
    make_goto_command,
    make_stop_command,
    make_emergency_stop,
)


class DroneController:
    """
    Desktop-side high-level drone command controller.

    Responsibility:
    - Send commands to ESP32 receiver on UDP port 5007
    - ESP32 executes/forwards commands
    - Desktop remains the navigation brain
    """

    def __init__(self, drone_ip="192.168.1.200", command_port=5007):
        self.drone_ip = drone_ip
        self.command_port = command_port
        self.sender = UDPSender(drone_ip, command_port)

    def send_packet(self, packet: dict):
        """
        Low-level safe send wrapper.
        """
        print(f"📤 Sending to drone {self.drone_ip}:{self.command_port} -> {packet}")
        self.sender.send(packet)

    def send_path(self, path: list, step: int = 25, delay: float = 0.08):
        """
        Send simplified path to ESP32.

        path format:
            [[lat, lon], [lat, lon], ...]

        step:
            send every Nth point to reduce UDP packet count.
        """

        if not path:
            print("⚠️ Cannot send empty path")
            return 0

        simplified_path = path[::step]

        if simplified_path[-1] != path[-1]:
            simplified_path.append(path[-1])

        self.send_packet(make_path_start(len(simplified_path)))
        time.sleep(delay)

        for index, point in enumerate(simplified_path):
            lat, lon = point
            self.send_packet(make_path_point(index, lat, lon))
            time.sleep(delay)

        self.send_packet(make_path_end())

        print(f"✅ Sent {len(simplified_path)} waypoints to drone")
        return len(simplified_path)

    def start_scan(self):
        self.send_packet(make_start_scan())

    def stop_scan(self):
        self.send_packet(make_stop_scan())

    def goto(self, lat: float, lon: float):
        """
        Desktop tells ESP32 current navigation target.
        ESP32 does not decide path; it only receives the target command.
        """
        self.send_packet(make_goto_command(lat, lon))

    def move(self, throttle=0.0, yaw=0.0, pitch=0.0, roll=0.0):
        """
        Movement command.

        Values should be normalized for now:
            throttle: 0.0 to 1.0
            yaw:     -1.0 to 1.0
            pitch:   -1.0 to 1.0
            roll:    -1.0 to 1.0
        """
        self.send_packet(
            make_manual_control(
                throttle=throttle,
                yaw=yaw,
                pitch=pitch,
                roll=roll,
            )
        )

    def stop(self):
        """
        Normal stop command.
        """
        self.send_packet(make_stop_command())

    def emergency_stop(self):
        """
        Emergency stop command.
        Later this should immediately cut movement commands safely.
        """
        self.send_packet(make_emergency_stop())

    def close(self):
        self.sender.close()