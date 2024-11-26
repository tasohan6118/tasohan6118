import socket
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import os


SERVER_HOST = "0.0.0.0"
SERVER_PORT = 9090
server_socket = None
is_running = False


def handle_client(client_socket):
    try:
        request = client_socket.recv(1500).decode()
        log_message(f"Received request:\n{request}")

        headers = request.split('\n')
        if len(headers) > 0:
            first_line = headers[0].split()
            if len(first_line) >= 2:
                method, path = first_line[0], first_line[1]
            else:
                client_socket.close()
                return


            if method == 'GET':
                if path == '/':
                    response = serve_file('index.html', "text/html")
                elif path == '/book':
                    response = serve_file('book.json', "application/json")
                else:
                    response = error_response(404, "404 Not Found")


            elif method == 'POST':
                if path == '/save':
                    body = request.split('\r\n\r\n')[1]
                    save_data(body)
                    response = "HTTP/1.1 200 OK\n\nData saved!"
                else:
                    response = error_response(404, "404 Not Found")


            else:
                response = error_response(405, "405 Method Not Allowed", allow="GET, POST")

            client_socket.sendall(response.encode())
    except Exception as e:
        log_message(f"Error handling request: {e}")
    finally:
        client_socket.close()


def serve_file(filepath, content_type):
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            content = file.read()
        return f"HTTP/1.1 200 OK\nContent-Type: {content_type}\n\n{content}"
    else:
        return error_response(404, "404 Not Found")


def save_data(data):
    with open('data.txt', 'a') as file:
        file.write(data + '\n')


def error_response(status_code, message, allow=None):
    headers = f"HTTP/1.1 {status_code}\nContent-Type: text/html\n"
    if allow:
        headers += f"Allow: {allow}\n"
    return f"{headers}\n\n<h1>{message}</h1>"


def start_server():
    global server_socket, is_running
    if is_running:
        log_message("Server is already running.")
        return

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((SERVER_HOST, SERVER_PORT))
        server_socket.listen(5)
        log_message(f"Server started on port {SERVER_PORT}...")
        is_running = True
        threading.Thread(target=accept_clients, daemon=True).start()
    except Exception as e:
        log_message(f"Error starting server: {e}")


def accept_clients():
    while is_running:
        try:
            client_socket, client_address = server_socket.accept()
            log_message(f"Connection from {client_address}")
            threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()
        except OSError:
            break


def stop_server():
    global server_socket, is_running
    if not is_running:
        log_message("Server is not running.")
        return

    is_running = False
    server_socket.close()
    log_message("Server stopped.")


def log_message(message):
    log_area.config(state=tk.NORMAL)
    log_area.insert(tk.END, message + "\n")
    log_area.config(state=tk.DISABLED)
    log_area.yview(tk.END)


def create_gui():
    window = tk.Tk()
    window.title("Advanced Web Server")
    window.geometry("750x550")
    window.config(bg="#1E1E1E")


    title = tk.Label(window, text="Advanced HTTP Web Server", font=("Helvetica", 20, "bold"), bg="#1E1E1E", fg="#61AFEF")
    title.pack(pady=15)


    button_frame = tk.Frame(window, bg="#1E1E1E")
    button_frame.pack(pady=10)


    start_button = tk.Button(button_frame, text="Start Server", command=start_server, bg="#98C379", fg="white", font=("Helvetica", 14), width=15)
    start_button.grid(row=0, column=0, padx=10)

    stop_button = tk.Button(button_frame, text="Stop Server", command=stop_server, bg="#E06C75", fg="white", font=("Helvetica", 14), width=15)
    stop_button.grid(row=0, column=1, padx=10)


    global log_area
    log_area = ScrolledText(window, height=20, width=90, state=tk.DISABLED, font=("Courier", 12), bg="#1E1E1E", fg="#D4D4D4", wrap=tk.WORD)
    log_area.pack(pady=15, padx=20, fill="both", expand=True)


    window.protocol("WM_DELETE_WINDOW", lambda: (stop_server(), window.destroy()))
    window.mainloop()


if __name__ == "__main__":
    create_gui()
