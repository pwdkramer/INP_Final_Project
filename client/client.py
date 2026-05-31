import socket
import threading

HOST = "127.0.0.1"
PORT = 5000

def listen_to_server(sock):
    """Background thread: receives messages from the server."""
    try:
        while True:
            data = sock.recv(1024)
            if not data:
                print("Disconnected from server.")
                break
            print(data.decode().strip())
    except Exception as e:
        print(f"[!] Error receiving data: {e}")
    finally:
        sock.close()

def main():
    # Connect to the server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a TCP/IP socket
    sock.connect((HOST, PORT))
    print(f"Connected to server at {HOST}:{PORT}")

    # Start background listener thread
    listener = threading.Thread(target=listen_to_server, args=(sock,), daemon=True)
    listener.start()

    # Main loop: send user input to server
    try:
        while True:
            msg = input()
            if not msg:
                continue

            sock.sendall((msg + "\r\n").encode())

            if msg.upper() == "QUIT":
                break

    except KeyboardInterrupt:
        print("\nClient shutting down.")

    finally:
        sock.close()

if __name__ == "__main__":
    main()
