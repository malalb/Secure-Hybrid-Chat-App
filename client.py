import socket
import threading
import random
import time
from datetime import datetime
from colorama import Fore, init, Style

init()  # Initiating colorama

# Define the color choices for the clients
colors = [Fore.BLUE, Fore.CYAN, Fore.GREEN,
          Fore.LIGHTBLACK_EX, Fore.LIGHTGREEN_EX, 
          Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, 
          Fore.LIGHTYELLOW_EX, Fore.MAGENTA]
client_color = random.choice(colors)  # Random color for client messages

# Set host and port for connectivity
host = 'localhost'
port = 9999

nickname = input("Choose your nickname: ")
password = input("Enter your password: ")

# Asking user to choose a region for IP addressing
print("Choose your region for IP address:")
print("A: 10.0.0.X\nB: 172.16.0.X\nC: 192.168.X.X")
region = input("Enter A, B, or C: ")

# Assigning IP based on region
if region.lower() == 'a':
    ip_address = f"10.0.0.{random.randint(1, 254)}"
    ip_public = '10.0.0.0'
elif region.lower() == 'b':
    ip_address = f"172.16.0.{random.randint(1, 254)}"
    ip_public = '172.16.0.0'
else:
    ip_address = f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"
    ip_public = '192.168.0.0'

client = None

def is_server_active(host, port):
    """Check if the server is active by attempting a quick socket connection."""
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.connect((host, port))
        probe.close()
        return True
    except socket.error:
        return False

def serve_clients(host, port):
    """Function to serve clients, effectively acting as a server."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()
    print("Server started.")

    clients = []  # List of clients

    def broadcast(message):
        """Function to broadcast messages to all connected clients."""
        for client, _, _, _ in clients:
            client.send(message.encode('utf-8'))

    def handle(client):
        """Function to handle individual client messages and disconnections."""
        while True:
            try:
                message = client[0].recv(1024).decode('utf-8')
                broadcast(message)
            except:
                clients.remove(client)
                client[0].close()
                broadcast(f'{client[1]} has left the chat.')
                break

    def receive():
        """Function to handle incoming client connections."""
        while True:
            client_socket,_ = server.accept()

            client_socket.send("NICK".encode('utf-8'))
            nickname = client_socket.recv(1024).decode('utf-8')
            client_socket.send("PASS".encode('utf-8'))
            password = client_socket.recv(1024).decode('utf-8')
            client_socket.send("IP".encode('utf-8'))
            ip_public = client_socket.recv(1024).decode('utf-8')
            print(f"Connected with {ip_public} ")

            # Check if existing user
            existing_user = next((client for client in clients if client[1] == nickname and client[2] == password and client[3] == ip_address), None)

            if existing_user:
                # Welcome back existing user
                client_socket.send("Welcome Back!".encode('utf-8'))
                print(f"{nickname} logged in")
                broadcast(f"{nickname} joined the chat again!")
            else:
                # Handle new user registration
                clients.append((client_socket, nickname, password, ip_address))
                client_socket.send("New User!".encode('utf-8'))
                print(f"New user signed up: {nickname} ")
                broadcast(f"{nickname} joined the chat!")

            thread = threading.Thread(target=handle, args=((client_socket, nickname, password, ip_address),))
            thread.start()

    receive()

def client_mode(host, port):
    """Client mode operation, attempts to connect to the server or become one."""
    global client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        print("Private IP :", ip_address)
        client.connect((host, port))
        print("Connected to the server.")
        def receive():
            """Receive messages from the server."""
            while True:
                try:
                    message = client.recv(1024).decode('utf-8')
                    if message == 'NICK':
                        client.send(nickname.encode('utf-8'))
                    elif message == 'PASS':
                        client.send(password.encode('utf-8'))
                    elif message == 'IP':
                        client.send(ip_public.encode('utf-8'))
                    else:
                        print(message)  # Print any other server messages
                except:
                    print("Connection lost. Attempting to reconnect or become a server...")
                    client.close()
                    attempt_to_become_server()
                    break

        def send():
            """Send messages to the server."""
            while True:
                message = input("")
                if message:
                    timestamp = datetime.now().strftime('%H:%M')
                    formatted_message = f'{client_color}[{timestamp}] {nickname}: {message}{Style.RESET_ALL}'
                    try:
                        client.send(formatted_message.encode('utf-8'))
                    except:
                        print("Failed to send message.")
                        break

        receive_thread = threading.Thread(target=receive)
        receive_thread.start()

        send_thread = threading.Thread(target=send)
        send_thread.start()

    except:
        print("Cannot connect to server. Attempting to become a server...")
        serve_clients(host, port)

def attempt_to_become_server():
    """Attempt to become a server if no active server is found."""
    global client
    if not is_server_active(host, port):
        print("No active server found. This client will now attempt to act as the server.")
        threading.Thread(target=serve_clients, args=(host, port)).start()
        time.sleep(1)  # Give server thread time to start
        client_mode(host, port)  # Reconnect as a client to own server
    else:
        print("Found an active server. Reconnecting...")
        client_mode(host, port)

client_mode(host, port)
