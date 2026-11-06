import socket
import threading
import logging
from protocol import send_msg, recv_msg

HOST, PORT = "0.0.0.0", 5000
clients = {}
lock = threading.Lock()

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")


def broadcast(msg, exclude=None):
    with lock:
        for name, conn in clients.items():
            if name != exclude:
                try:
                    send_msg(conn, msg)
                except OSError:
                    pass


def send_to(name, msg):
    with lock:
        conn = clients.get(name)
        if conn is None:
            return False
        try:
            send_msg(conn, msg)
        except OSError:
            return False
    return True


def handle_client(conn, addr):
    name = None
    try:
        username = recv_msg(conn).get("text", "").strip()
        with lock:
            taken = (not username) or (username in clients)
            if not taken:
                clients[username] = conn
        if taken:
            send_msg(conn, {"type": "system",
                            "text": "Username empty or already taken."})
            return
        name = username

        logging.info("%s joined from %s", name, addr)
        send_msg(conn, {"type": "system",
                        "text": f"Welcome {name}! Commands: /list /msg <user> <text> /quit"})
        broadcast({"type": "system", "text": f"{name} joined"}, exclude=name)

        while True:
            text = recv_msg(conn).get("text", "").strip()
            if not text:
                continue

            if text == "/quit":
                break
            elif text == "/list":
                with lock:
                    online = ", ".join(clients)
                send_to(name, {"type": "system", "text": f"Online: {online}"})
            elif text.startswith("/msg "):
                parts = text.split(" ", 2)
                if len(parts) < 3:
                    send_to(name, {"type": "system",
                                   "text": "Usage: /msg <user> <text>"})
                elif not send_to(parts[1], {"type": "private",
                                            "from": name, "text": parts[2]}):
                    send_to(name, {"type": "system",
                                   "text": f"User '{parts[1]}' not found."})
            else:
                broadcast({"type": "chat", "from": name, "text": text},
                          exclude=name)

    except (ConnectionError, OSError, ValueError) as e:
        logging.warning("Connection problem with %s: %s", addr, e)
    finally:
        if name:
            with lock:
                clients.pop(name, None)
            broadcast({"type": "system", "text": f"{name} left"})
            logging.info("%s left", name)
        conn.close()


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    logging.info("Server listening on port %d", PORT)
    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr),
                             daemon=True).start()
    except KeyboardInterrupt:
        logging.info("Shutting down")
    finally:
        server.close()


if __name__ == "__main__":
    main()