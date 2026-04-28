import socket
from backend.drone_comm.drone_protocol import encode_packet


class UDPSender:
    def __init__(self, target_ip: str, target_port: int):
        self.target_ip = target_ip
        self.target_port = target_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, packet: dict):
        data = encode_packet(packet)
        self.sock.sendto(data, (self.target_ip, self.target_port))
        print(f"📡 UDP sent to {self.target_ip}:{self.target_port} -> {packet}")

    def close(self):
        self.sock.close()