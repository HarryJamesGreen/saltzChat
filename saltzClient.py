import socket
from cryptography.fernet import Fernet
import colorama
from colorama import Fore, Style
import threading

colorama.init()

def receive_messages(client_socket, cipher):
    try:
        while True:
            msg = client_socket.recv(1024)
            if msg:
                decrypted_msg = cipher.decrypt(msg).decode('utf-8')
                print(Fore.CYAN + decrypted_msg + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + "Lost connection to the server: " + str(e) + Style.RESET_ALL)

def start_client():
    host = 'localhost'
    port = 6000
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    print(Fore.GREEN + "Connected to the server." + Style.RESET_ALL)

    key = client_socket.recv(1024)
    cipher = Fernet(key)

    username = input(Fore.YELLOW + "Enter your username: " + Style.RESET_ALL)
    client_socket.send(username.encode('utf-8'))

    threading.Thread(target=receive_messages, args=(client_socket, cipher), daemon=True).start()

    print(Fore.LIGHTBLUE_EX + "Type '/who' to see online users, '/private [username] [message]' for private messages, or 'exit' to quit. Start chatting!" + Style.RESET_ALL)
    while True:
        try:
            msg = input()
            if msg.lower() == 'exit':
                break
            elif msg.startswith("/private"):
                parts = msg.split(maxsplit=2)
                if len(parts) < 3:
                    print(Fore.RED + "Error: Invalid private message format. Use '/private [username] [message]'." + Style.RESET_ALL)
                    continue
                target_user, private_msg = parts[1], parts[2]
                formatted_msg = f"/private {target_user} {username}: {private_msg}"
                client_socket.send(cipher.encrypt(formatted_msg.encode('utf-8')))
            elif msg == "/who":
                client_socket.send(cipher.encrypt("/who".encode('utf-8')))
            else:
                formatted_msg = f"{username}: {msg}"
                client_socket.send(cipher.encrypt(formatted_msg.encode('utf-8')))
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(Fore.RED + f"Unexpected error: {e}" + Style.RESET_ALL)

    client_socket.close()
    print(Fore.RED + "Disconnected from the server." + Style.RESET_ALL)

if __name__ == "__main__":
    start_client()
