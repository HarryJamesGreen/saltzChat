import socket
import threading
from cryptography.fernet import Fernet
from datetime import datetime

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def handle_client(client_socket, addr, cipher, connections, usernames):
    username = None
    try:
        username = client_socket.recv(1024).decode('utf-8')
        usernames[client_socket] = username
        welcome_message = f"[{timestamp()}] SYSTEM: {username} has joined the chat!"
        print(welcome_message)
        broadcast_message(welcome_message, connections, cipher)

        while True:
            msg = client_socket.recv(1024)
            if msg:
                decrypted_msg = cipher.decrypt(msg).decode('utf-8')
                if decrypted_msg.startswith("/private"):
                    _, target_username, private_msg = decrypted_msg.split(maxsplit=2)
                    target_socket = next((s for s, u in usernames.items() if u == target_username), None)
                    if target_socket:
                        encrypted_private_msg = cipher.encrypt(f"Private from {username}: {private_msg}".encode('utf-8'))
                        target_socket.send(encrypted_private_msg)
                    else:
                        error_msg = "User not found."
                        client_socket.send(cipher.encrypt(error_msg.encode('utf-8')))
                elif decrypted_msg == "/who":
                    online_users = ', '.join(usernames.values())
                    client_socket.send(cipher.encrypt(f"Online users: {online_users}".encode('utf-8')))
                else:
                    formatted_message = f"[{timestamp()}] {username}: {decrypted_msg}"
                    print(formatted_message)
                    broadcast_message(formatted_message, connections, cipher)
    except Exception as e:
        print(f"[{timestamp()}] Error with {username or 'an unknown user'}: {e}")
    finally:
        if client_socket in connections:
            connections.remove(client_socket)
        leave_message = f"[{timestamp()}] SYSTEM: {username} has left the chat." if username else "An unknown user has disconnected."
        print(leave_message)
        broadcast_message(leave_message, connections, cipher)
        client_socket.close()
        if client_socket in usernames:
            del usernames[client_socket]

def broadcast_message(message, connections, cipher):
    encrypted_message = cipher.encrypt(message.encode('utf-8'))
    for conn in connections:
        conn.send(encrypted_message)

def start_server():
    key = Fernet.generate_key()
    cipher = Fernet(key)
    host = 'localhost'
    port = 6000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"Server is running on {host}:{port}")
    connections = []
    usernames = {}

    try:
        while True:
            client_socket, addr = server_socket.accept()
            print(f"New connection from {addr}")
            client_socket.send(key)
            connections.append(client_socket)
            threading.Thread(target=handle_client, args=(client_socket, addr, cipher, connections, usernames)).start()
    except KeyboardInterrupt:
        print("Server is shutting down.")
    finally:
        for conn in connections:
            conn.close()
        server_socket.close()

if __name__ == "__main__":
    start_server()
