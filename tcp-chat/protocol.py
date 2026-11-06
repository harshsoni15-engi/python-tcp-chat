import json
import struct

MAX_SIZE = 1_000_000


def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed")
        buf += chunk
    return buf


def send_msg(sock, data: dict):
    payload = json.dumps(data).encode()
    sock.sendall(struct.pack("!I", len(payload)) + payload)


def recv_msg(sock) -> dict:
    (length,) = struct.unpack("!I", recv_exact(sock, 4))
    if length > MAX_SIZE:
        raise ValueError("Message too large")
    return json.loads(recv_exact(sock, length).decode())