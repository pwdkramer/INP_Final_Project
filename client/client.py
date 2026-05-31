import socket
import threading

HOST = "127.0.0.1"
PORT = 5000

connected = True

def listen_to_server(sock):
    """Background thread: receives messages from the server."""
    global connected
    try:
        while True:
            data = sock.recv(1024)
            if not data:
                print("Disconnected from server.")
                connected = False
                break
            print(data.decode().strip())
    except:
        connected = False
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
        while connected:
            msg = input()
            if not msg:
                continue

            if not connected:
                print("Not connected to server. Exiting.")
                break

            sock.sendall((msg + "\r\n").encode())

            if msg.upper() == "QUIT":
                break

    except KeyboardInterrupt:
        print("\nClient shutting down.")

    finally:
        sock.close()

if __name__ == "__main__":
    main()
