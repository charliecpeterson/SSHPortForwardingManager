import tkinter as tk
from tkinter import messagebox
import subprocess
import json
import os

class PortForwardingApp:
    def __init__(self, root):
        # Initialize the Tkinter root window
        self.root = root
        self.root.title("SSH Port Forwarding Manager")
        
        # Initialize connections dictionary to store connection details
        self.entries = []
        self.connections = {}
        
        # Load saved connections from file
        self.load_saved_connections()
        
        # Create input fields for connection details
        self.create_input_fields()
        
        # Frame to display the list of connections
        self.connections_frame = tk.Frame(root)
        self.connections_frame.pack(pady=10)
        self.update_connections_list()
        
        # Buttons to add new connection and save connections to file
        tk.Button(root, text="Add Connection", command=self.add_connection).pack(pady=5)
        tk.Button(root, text="Save Connections", command=self.save_connections).pack(pady=5)
        
        # Set protocol for window close to handle cleanup
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_input_fields(self):
        # Create and place input fields for connection details
        frame = tk.Frame(self.root)
        frame.pack(pady=10)
        
        tk.Label(frame, text="Username").grid(row=0, column=0)
        tk.Label(frame, text="Local Port").grid(row=0, column=1)
        tk.Label(frame, text="Remote Port").grid(row=0, column=2)
        tk.Label(frame, text="Remote Host").grid(row=0, column=3)
        tk.Label(frame, text="Remote Bind Address (optional)").grid(row=0, column=4)
        tk.Label(frame, text="Password").grid(row=0, column=5)
        
        self.username_entry = tk.Entry(frame)
        self.local_port_entry = tk.Entry(frame)
        self.remote_port_entry = tk.Entry(frame)
        self.remote_host_entry = tk.Entry(frame)
        self.remote_bind_entry = tk.Entry(frame)
        self.password_entry = tk.Entry(frame, show='*')
        
        self.username_entry.grid(row=1, column=0)
        self.local_port_entry.grid(row=1, column=1)
        self.remote_port_entry.grid(row=1, column=2)
        self.remote_host_entry.grid(row=1, column=3)
        self.remote_bind_entry.grid(row=1, column=4)
        self.password_entry.grid(row=1, column=5)

    def add_connection(self):
        # Gather input data from user
        username = self.username_entry.get()
        local_port = self.local_port_entry.get()
        remote_port = self.remote_port_entry.get()
        remote_host = self.remote_host_entry.get()
        remote_bind = self.remote_bind_entry.get() or "localhost"
        password = self.password_entry.get()
        
        # Validate required fields
        if not username or not local_port or not remote_port or not remote_host:
            messagebox.showerror("Input Error", "All fields except password and remote bind address are required!")
            return
        
        # Create a unique connection ID
        connection_id = f"{username}@{remote_host}:{local_port}->{remote_bind}:{remote_port}"
        if connection_id in self.connections:
            messagebox.showerror("Duplicate Error", "This connection already exists!")
            return
        
        # Store connection details in the dictionary
        self.connections[connection_id] = {
            'username': username,
            'local_port': local_port,
            'remote_port': remote_port,
            'remote_host': remote_host,
            'remote_bind': remote_bind,
            'password': password,
            'process': None  # Initialize process as None
        }
        
        # Update the list of connections and clear input fields
        self.update_connections_list()
        self.clear_input_fields()
    
    def clear_input_fields(self):
        # Clear all input fields
        self.username_entry.delete(0, tk.END)
        self.local_port_entry.delete(0, tk.END)
        self.remote_port_entry.delete(0, tk.END)
        self.remote_host_entry.delete(0, tk.END)
        self.remote_bind_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)

    def update_connections_list(self):
        # Clear the current list of connections
        for widget in self.connections_frame.winfo_children():
            widget.destroy()
        
        # Display all connections with their status and control buttons
        for connection_id, details in self.connections.items():
            frame = tk.Frame(self.connections_frame)
            frame.pack(fill='x', pady=2)
            
            tk.Label(frame, text=connection_id).pack(side='left')
            
            status_label = tk.Label(frame, text="Stopped", fg='red')
            status_label.pack(side='left', padx=10)
            
            start_button = tk.Button(frame, text="Start", command=lambda cid=connection_id, sl=status_label: self.start_connection(cid, sl))
            start_button.pack(side='left')
            
            stop_button = tk.Button(frame, text="Stop", command=lambda cid=connection_id, sl=status_label: self.stop_connection(cid, sl))
            stop_button.pack(side='left')
    
    def start_connection(self, connection_id, status_label):
        # Start the SSH port forwarding connection
        details = self.connections[connection_id]
        username = details['username']
        local_port = details['local_port']
        remote_port = details['remote_port']
        remote_host = details['remote_host']
        remote_bind = details['remote_bind']
        password = details['password']
        
        command = f"ssh -L {local_port}:{remote_bind}:{remote_port} {username}@{remote_host}"
        
        if password:
            command = f"sshpass -p {password} {command}"
        
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.connections[connection_id]['process'] = proc
        status_label.config(text="Running", fg='green')
    
    def stop_connection(self, connection_id, status_label):
        # Stop the SSH port forwarding connection
        proc = self.connections[connection_id].get('process')
        if proc:
            proc.terminate()
            self.connections[connection_id]['process'] = None
            status_label.config(text="Stopped", fg='red')
    
    def save_connections(self):
        # Save connections to a JSON file, excluding the process objects
        save_data = {k: {key: value for key, value in v.items() if key != 'process'} for k, v in self.connections.items()}
        with open("connections.json", "w") as file:
            json.dump(save_data, file)
        messagebox.showinfo("Save", "Connections saved successfully!")
    
    def load_saved_connections(self):
        # Load connections from a JSON file and set process to None
        if os.path.exists("connections.json"):
            try:
                with open("connections.json", "r") as file:
                    self.connections = json.load(file)
                    if not isinstance(self.connections, dict):
                        self.connections = {}
                for k in self.connections:
                    self.connections[k]['process'] = None
            except json.JSONDecodeError:
                messagebox.showerror("Load Error", "Failed to load connections. The file is corrupted.")
                self.connections = {}
    
    def on_closing(self):
        # Handle cleanup when the window is closed
        for connection_id, details in self.connections.items():
            proc = details.get('process')
            if proc:
                proc.terminate()
        
        self.root.destroy()

if __name__ == "__main__":
    # Create the main window and start the application
    root = tk.Tk()
    app = PortForwardingApp(root)
    root.mainloop()

