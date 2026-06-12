import socket
import threading
import signal

shutting_down = False

HOST = "0.0.0.0"
PORT = 5000

rooms = {}              # room_name -> set of client_ids
client_ids = {}         # conn -> string client_id (e.g. "client0", "client1", etc.)
next_client_id = 0

def handle_signal(sig, frame):
    global shutting_down
    print("\n[!] Signal received, shutting down server...")
    shutting_down = True

signal.signal(signal.SIGINT, handle_signal)


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
        handle_join(args, conn)

    elif command == "LEAVE":
        # Handle LEAVE command
        handle_leave(args, conn)

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
    room_names = list(rooms.keys()) # Get the list of room names (keys of the rooms dictionary)
    response = "OK LIST\n" + "\n".join(room_names) + "\r\n"
    conn.sendall(response.encode())


def handle_create(args, conn):
    room = args.strip()
    if not room:
        conn.sendall(b"ERR_INVALID_ARGS\r\n")
        return
    
    if room in rooms:
        conn.sendall(b"ERR_ROOM_ALREADY_EXISTS\r\n")
        return
    
    rooms[room] = set() # Create a new room with an empty set of members
    conn.sendall(f"OK ROOM_CREATED {room}\r\n".encode())


def handle_join(args, conn):
    room = args.strip()
    if not room:
        conn.sendall(b"ERR_INVALID_ARGS\r\n")
        return
    
    if room not in rooms:
        conn.sendall(b"ERR_NO_SUCH_ROOM\r\n")
        return
    
    if conn in rooms[room]:
        conn.sendall(b"ERR_ALREADY_IN_ROOM\r\n")
        return
    
    rooms[room].add(conn)
    client_id = client_ids[conn]

    conn.sendall(f"OK ROOM_JOINED {room}\r\n".encode())

    notice = f"NOTICE {room} {client_id} has joined the room\r\n".encode()
    for member in rooms[room]:
        if member != conn:
            try:
                member.sendall(notice)
            except:
                cleanup_client(member)


def handle_leave(args, conn):
    room = args.strip()
    if not room:
        conn.sendall(b"ERR_INVALID_ARGS\r\n")
        return
    
    if room not in rooms:
        conn.sendall(b"ERR_NO_SUCH_ROOM\r\n")
        return
    
    if conn not in rooms[room]:
        conn.sendall(b"ERR_NOT_IN_ROOM\r\n")
        return
    
    rooms[room].remove(conn)
    client_id = client_ids[conn]

    conn.sendall(f"OK LEFT_ROOM {room}\r\n".encode())

    notice = f"NOTICE {room} {client_id} has left the room\r\n".encode()
    for member in rooms[room]:
        try:
            member.sendall(notice)
        except:
            cleanup_client(member)


def handle_members(args, conn):
    room = args.strip()
    if not room:
        conn.sendall(b"ERR_INVALID_ARGS\r\n")
        return
    
    if room not in rooms:
        conn.sendall(b"ERR_NO_SUCH_ROOM\r\n")
        return
    
    members = rooms[room]
    member_ids = [client_ids[m] for m in members]

    response = f"OK MEMBERS {room}\n" + "\n".join(member_ids) + "\r\n"
    conn.sendall(response.encode())


def handle_send(args, conn):
    parts = args.split(" ", 1) # split into room and message (only on the first space)

    if len(parts) < 2:
        conn.sendall(b"ERR_INVALID_ARGS\r\n")
        return
    
    room = parts[0].strip()
    message = parts[1]

    if room not in rooms:
        conn.sendall(b"ERR_NO_SUCH_ROOM\r\n")
        return
    
    if conn not in rooms[room]:
        conn.sendall(b"ERR_NOT_IN_ROOM\r\n")
        return
    
    sender_id = client_ids[conn]

    # Broadcast the message to all members of the room (including sender)
    broadcast = f"MSG {room} {sender_id} - {message}\r\n".encode()
    for member in rooms[room]:
        try:
            member.sendall(broadcast)
        except:
            cleanup_client(member)

    conn.sendall(f"OK MSG_SENT {room}\r\n".encode())


def cleanup_client(conn):
    client_id = client_ids.get(conn)

    # Remove client from all rooms
    for room, members in list(rooms.items()):
        if conn in members:
            members.remove(conn)

            # Notify other members that the client has left
            notice = f"NOTICE {room} {client_id} has left the room\r\n".encode()
            for member in members:
                member.sendall(notice)

    if conn in client_ids:
        del client_ids[conn]

def handle_quit(conn):
    conn.sendall(b"OK QUIT\r\n")
    cleanup_client(conn)
    conn.close()


def handle_client(conn, addr):
    print(f"[+] Client connected: {addr}")

    global next_client_id
    client_id = f"client{next_client_id}"
    next_client_id += 1
    client_ids[conn] = client_id

    print(f"[+] Assigned client ID {client_id} to {addr}")

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
        cleanup_client(conn)


def start_server():
    print(f"[*] Starting server on {HOST}:{PORT}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # AF_INET = IPv4, SOCK_STREAM = TCP (Create a TCP/IP socket)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allow reuse of the address (avoid "Address already in use" error on restart)
        s.bind((HOST, PORT))
        s.listen()
        s.settimeout(1.0) # Set a timeout for the accept() call to allow periodic shutdown checks

        print("[*] Server is running. Waiting for connections...")

        while True:
            try:
                conn, addr = s.accept()
            except socket.timeout:
                if shutting_down:
                    break
                continue

            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True) # Create a new thread to handle the client connection (daemon=True means it will exit when the main thread exits)
            thread.start()

        for conn in list(client_ids.keys()):
            try:
                conn.sendall(b"NOTICE SERVER_SHUTDOWN\r\n")
            except:
                pass
            conn.close()


if __name__ == "__main__":
    start_server()
