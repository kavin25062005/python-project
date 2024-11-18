import os
import socket
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import qrcode
import firebase_admin
from firebase_admin import credentials, storage
from PIL import Image, ImageTk
from cryptography.fernet import Fernet

# Generate or load a valid Fernet key (32-byte base64 URL-safe encoded)
fernet_key = Fernet.generate_key()  # Replace this with the actual key if already generated and saved
cipher_suite = Fernet(fernet_key)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("C:\\Users\\navee\\OneDrive\\Desktop\\python project\\credentials.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'panda-file-share.appspot.com'
})

# File Transfer App class
class FileTransferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Transfer App - ShareIt Clone")
        self.root.geometry("400x600")

        # Create tab control
        tab_control = ttk.Notebook(root)

        # Server Tab
        self.server_tab = ttk.Frame(tab_control)
        tab_control.add(self.server_tab, text="Server")

        # Client Tab
        self.client_tab = ttk.Frame(tab_control)
        tab_control.add(self.client_tab, text="Client")

        # Cloud Upload Tab
        self.cloud_tab = ttk.Frame(tab_control)
        tab_control.add(self.cloud_tab, text="Cloud Upload")

        # Cloud Download Tab
        self.download_tab = ttk.Frame(tab_control)
        tab_control.add(self.download_tab, text="Cloud Download")

        tab_control.pack(expand=1, fill="both")

        ### SERVER UI COMPONENTS ###
        self.server_label = tk.Label(self.server_tab, text="Server Mode: Ready to receive files", font=("Arial", 12))
        self.server_label.pack(pady=20)

        self.start_server_button = tk.Button(self.server_tab, text="Start Server", command=self.start_server, font=("Arial", 12))
        self.start_server_button.pack(pady=10)

        self.server_status_label = tk.Label(self.server_tab, text="Status: Waiting...", font=("Arial", 10))
        self.server_status_label.pack(pady=10)

        ### CLIENT UI COMPONENTS ###
        self.client_label = tk.Label(self.client_tab, text="Client Mode: Select a file to send", font=("Arial", 12))
        self.client_label.pack(pady=20)

        self.browse_button = tk.Button(self.client_tab, text="Browse File", command=self.browse_file, font=("Arial", 12))
        self.browse_button.pack(pady=10)

        self.file_label = tk.Label(self.client_tab, text="No file selected", font=("Arial", 10))
        self.file_label.pack(pady=10)

        self.send_button = tk.Button(self.client_tab, text="Send File", command=self.send_file, state=tk.DISABLED, font=("Arial", 12))
        self.send_button.pack(pady=10)

        self.client_status_label = tk.Label(self.client_tab, text="Status: Waiting...", font=("Arial", 10))
        self.client_status_label.pack(pady=10)

        ### CLOUD UPLOAD UI COMPONENTS ###
        self.cloud_label = tk.Label(self.cloud_tab, text="Cloud Upload: Select a file to upload", font=("Arial", 12))
        self.cloud_label.pack(pady=20)

        self.cloud_browse_button = tk.Button(self.cloud_tab, text="Browse File", command=self.browse_cloud_file, font=("Arial", 12))
        self.cloud_browse_button.pack(pady=10)

        self.cloud_file_label = tk.Label(self.cloud_tab, text="No file selected", font=("Arial", 10))
        self.cloud_file_label.pack(pady=10)

        self.upload_button = tk.Button(self.cloud_tab, text="Upload to Cloud", command=self.upload_to_cloud, state=tk.DISABLED, font=("Arial", 12))
        self.upload_button.pack(pady=10)

        self.cloud_status_label = tk.Label(self.cloud_tab, text="Status: Waiting...", font=("Arial", 10))
        self.cloud_status_label.pack(pady=10)

        self.qr_code_label = tk.Label(self.cloud_tab)
        self.qr_code_label.pack(pady=10)

        self.file_path = ""  # To store selected file path

        ### CLOUD DOWNLOAD UI COMPONENTS ###
        self.download_label = tk.Label(self.download_tab, text="Cloud Download: Select a file by number", font=("Arial", 12))
        self.download_label.pack(pady=20)

        self.file_listbox = tk.Listbox(self.download_tab, width=50, height=10)
        self.file_listbox.pack(pady=10)

        self.download_button = tk.Button(self.download_tab, text="Download File", command=self.download_file, font=("Arial", 12))
        self.download_button.pack(pady=10)

        self.download_status_label = tk.Label(self.download_tab, text="", font=("Arial", 10))
        self.download_status_label.pack(pady=10)

        self.generate_storage_qr()
        self.list_files_in_firebase()  # Fetch and display files on startup

    ### SERVER FUNCTIONS ###
    def start_server(self):
        self.server_status_label.config(text="Starting server, waiting for connections...")
        threading.Thread(target=self.server_thread).start()

    def server_thread(self):
        host = '0.0.0.0'  # Accept connections from any IP
        port = 5001
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(1)

        conn, addr = server_socket.accept()  # Wait for connection
        self.server_status_label.config(text=f"Connected by {addr}")

        file_name = conn.recv(1024).decode()
        with open(file_name, 'wb') as file:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                file.write(data)

        conn.close()
        self.server_status_label.config(text="File received successfully.")

    ### CLIENT FUNCTIONS ###
    def browse_file(self):
        self.file_path = filedialog.askopenfilename()
        if self.file_path:
            self.file_label.config(text=self.file_path)
            self.send_button.config(state=tk.NORMAL)

    def send_file(self):
        host = '127.0.0.1'  # Server IP address
        port = 5001
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))

        file_name = os.path.basename(self.file_path)
        client_socket.send(file_name.encode())

        with open(self.file_path, 'rb') as file:
            data = file.read(1024)
            while data:
                client_socket.send(data)
                data = file.read(1024)

        client_socket.close()
        self.client_status_label.config(text="File sent successfully.")

    ### CLOUD UPLOAD FUNCTIONS ###
    def browse_cloud_file(self):
        self.file_path = filedialog.askopenfilename()
        if self.file_path:
            self.cloud_file_label.config(text=self.file_path)
            self.upload_button.config(state=tk.NORMAL)

    def upload_to_cloud(self):
        bucket = storage.bucket()
        file_name = os.path.basename(self.file_path)
        blob = bucket.blob(file_name)
        blob.upload_from_filename(self.file_path)

        self.cloud_status_label.config(text="File uploaded successfully.")
        self.generate_storage_qr()

    ### GENERATE QR CODE ###
    def generate_storage_qr(self):
        bucket = storage.bucket()
        blobs = bucket.list_blobs()
        qr_content = '\n'.join([blob.name for blob in blobs])

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)

        qr_img = qr.make_image(fill='black', back_color='white')
        qr_img.save("storage_qr.png")

        img = Image.open("storage_qr.png")
        img = img.resize((200, 200))
        img_tk = ImageTk.PhotoImage(img)

        self.qr_code_label.config(image=img_tk)
        self.qr_code_label.image = img_tk  # Keep a reference to avoid garbage collection

    ### CLOUD DOWNLOAD FUNCTIONS ###
    def list_files_in_firebase(self):
        bucket = storage.bucket()
        blobs = bucket.list_blobs()

        self.file_listbox.delete(0, tk.END)
        for idx, blob in enumerate(blobs):
            self.file_listbox.insert(tk.END, f"{idx + 1}. {blob.name}")

    def download_file(self):
        selected_file = self.file_listbox.get(tk.ANCHOR)
        if not selected_file:
            return

        bucket = storage.bucket()
        blob = bucket.blob(selected_file.split(". ", 1)[-1])
        save_path = filedialog.asksaveasfilename(defaultextension="*", initialfile=blob.name)

        if save_path:
            blob.download_to_filename(save_path)
            self.download_status_label.config(text="File downloaded successfully.")

# Initialize the app
root = tk.Tk()
app = FileTransferApp(root)
root.mainloop()
