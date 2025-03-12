import socket
import threading

def serve_clients(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()

    clients = []
    nicknames = []

    def broadcast(message):
        for client in clients[:]:  # Iterate over a copy of the list to avoid modification during iteration
            try:
                client.send(message.encode('utf-8'))
            except Exception:
                print(f"Failed to send message")
                clients.remove(client)
                client.close()

    def handle(client):
        while True:
            try:
                message = client.recv(1024).decode('utf-8')
                broadcast(message)
            except Exception:
                print(f"Error with client")
                try:
                    index = clients.index(client)
                    nickname = nicknames[index][0]
                    broadcast(f'{nickname} left!')
                    clients.remove(client)
                    nicknames.pop(index)
                    client.close()
                except Exception:
                    print("Trying to clean up client.....")
                break

    def receive():
        while True:
            client, _ = server.accept()

            client.send("NICK".encode('utf-8'))
            nickname = client.recv(1024).decode('utf-8')
            client.send("PASS".encode('utf-8'))
            password = client.recv(1024).decode('utf-8')
            client.send("IP".encode('utf-8'))
            ip_public = client.recv(1024).decode('utf-8')

            user_id = (nickname, ip_public)
            existing_user = next((x for x in nicknames if x[0] == user_id[0] and x[2] == user_id[1]), None)

            if existing_user:
                if existing_user[1] != password:
                    client.send('Wrong password. Please try again.'.encode('utf-8'))
                    client.close()
                    continue
                client.send("Welcome Back!".encode('utf-8'))
                print(f"{nickname} Logged in again. with IP: {ip_public}")
                broadcast(f"{nickname} joined the chat again!")
            else:
                nicknames.append((user_id[0], password, user_id[1]))
                clients.append(client)
                client.send("Welcome to the chat!".encode('utf-8'))
                broadcast(f"{nickname} joined the chat!")
                print(f"New user signed up: {nickname} with IP: {ip_public}")

            thread = threading.Thread(target=handle, args=(client,))
            thread.start()

    receive()

host = 'localhost'
port = 9999
serve_clients(host, port)
