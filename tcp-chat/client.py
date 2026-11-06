import argparse
import socket
import threading
from protocol import send_msg, recv_msg


def receive(sock):
    try:
        while True:
            msg = recv_msg(sock)
            kind = msg.get("type")
            if kind == "chat":
                print(f"\n{msg['from']}: {msg['text']}")
            elif kind == "private":
                print(f"\n[private] {msg['from']}: {msg['text']}")
            else:
                print(f"\n* {msg['text']}")
    except (ConnectionError, OSError, ValueError):
        print("\nDisconnected. Press Enter to exit.")


def main():
    parser = argparse.ArgumentParser(description="TCP chat client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    username = input("Username: ").strip()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((args.host, args.port))
    send_msg(sock, {"text": username})

    threading.Thread(target=receive, args=(sock,), daemon=True).start()

    try:
        while True:
            text = input()
            send_msg(sock, {"text": text})
            if text == "/quit":
                break
    except (EOFError, KeyboardInterrupt, OSError):
        pass
    finally:
        sock.close()


if __name__ == "__main__":
    main()