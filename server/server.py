import socket
import threading

HOST = "0.0.0.0"
PORT = 5000

def parse_command(line):
    parts = line.split(" ", 1) # only split on the first space to separate command and arguments
    command = parts[0].upper()
    args = parts[1] if len(parts) > 1 else ""
    return command, args


def handle_command(command, args, conn, addr):
    if command == "LIST":
        # Handle LIST command
        handle_list(conn)

    elif command == "CREATE":
        # Handle CREATE command
        handle_create(args, conn)
        
    elif command == "JOIN":
        # Handle JOIN command
        handle_join(args, conn, addr)

    elif command == "LEAVE":
        # Handle LEAVE command
        handle_leave(args, conn, addr)
        
    elif command == "MEMBERS":
        # Handle MEMBERS command
        handle_members(args, conn)
        
    elif command == "SEND":
        # Handle SEND command
        handle_send(args, conn, addr)
        
    elif command == "QUIT":
        # Handle QUIT command
        handle_quit(conn, addr)

    else:
        conn.sendall(b"ERR_UNKNOWN_COMMAND\r\n")


def handle_list(conn):
    conn.sendall(b"OK LIST (not implemented yet)\r\n")
    

def handle_create(args, conn):
    conn.sendall(b"OK CREATE (not implemented yet)\r\n")


def handle_join(args, conn, addr):
    conn.sendall(b"OK JOIN (not implemented yet)\r\n")


def handle_leave(args, conn, addr):
    conn.sendall(b"OK LEAVE (not implemented yet)\r\n")


def handle_members(args, conn):
    conn.sendall(b"OK MEMBERS (not implemented yet)\r\n")


def handle_send(args, conn, addr):
    conn.sendall(b"OK SEND (not implemented yet)\r\n")


def handle_quit(conn, addr):
    conn.sendall(b"OK QUIT\r\n")
    conn.close()



def handle_client(conn, addr):
    print(f"[+] Client connected: {addr}")

    try:
        with conn:
            while True:
                data = conn.recv(1024) # Receive data from the client (up to 1024 bytes)
                if not data:
                    break  # client disconnected

                line = data.decode().strip()
                print(f"[{addr}] {line}")

                # # Temporary echo (replace with command parser later)
                # conn.sendall(f"OK ECHO {line}\r\n".encode())

                command, args = parse_command(line)
                handle_command(command, args, conn, addr)

    except Exception as e:
        print(f"[!] Error with client {addr}: {e}")

    finally:
        print(f"[-] Client disconnected: {addr}")


def start_server():
    print(f"[*] Starting server on {HOST}:{PORT}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # AF_INET = IPv4, SOCK_STREAM = TCP (Create a TCP/IP socket)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow reuse of the address (avoid "Address already in use" error on restart)
        s.bind((HOST, PORT))
        s.listen()

        print("[*] Server is running. Waiting for connections...")

        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True) # Create a new thread to handle the client connection (daemon=True means it will exit when the main thread exits)
            thread.start()


if __name__ == "__main__":
    start_server()
