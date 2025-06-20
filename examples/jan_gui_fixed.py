from datetime import datetime
import json
import os
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, filedialog

import requests
from src.core.logging_config import get_logger, setup_logging

class JanAssistantGUI:
    def __init__(self):
        self.api_base = "http://127.0.0.1:1337/v1"
        self.api_key = "124578"
        self.model = "qwen3:30b-a3b"
        setup_logging()
        self.logger = get_logger(self.__class__.__name__)
        self.conversation_history = []
        self.memory_file = "jan_memory.json"
        self.memory = self.load_memory()
        self.setup_gui()
    
    def load_memory(self):
        """Load memory from file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(
                "Error loading memory",
                extra={"extra_fields": {"error": str(e)}},
            )
        return {}
    
    def save_memory(self):
        """Save memory to file"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            self.logger.error(
                "Error saving memory",
                extra={"extra_fields": {"error": str(e)}},
            )
    
    def setup_gui(self):
        """Create the GUI interface"""
        self.root = tk.Tk()
        self.root.title("🤖 Jan Assistant with Tools")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="🤖 Jan Assistant with Tools", 
                              font=('Arial', 16, 'bold'), bg='#2b2b2b', fg='#ffffff')
        title_label.pack(pady=(0, 10))
        
        # Chat display frame with scrollbar
        chat_frame = tk.Frame(main_frame, bg='#2b2b2b')
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Text widget with manual scrollbar (avoiding ScrolledText)
        self.chat_display = tk.Text(
            chat_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            bg='#1e1e1e',
            fg='#ffffff',
            font=('Consolas', 10),
            state=tk.DISABLED
        )
        
        # Manual scrollbar
        scrollbar = tk.Scrollbar(chat_frame, command=self.chat_display.yview)
        self.chat_display.config(yscrollcommand=scrollbar.set)
        
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Input frame
        input_frame = tk.Frame(main_frame, bg='#2b2b2b')
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # User input
        self.user_input = tk.Entry(
            input_frame, 
            font=('Arial', 12),
            bg='#3c3c3c',
            fg='#ffffff',
            insertbackground='#ffffff'
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.user_input.bind('<Return>', self.send_message)
        
        # Send button
        self.send_button = tk.Button(
            input_frame, 
            text="Send", 
            command=self.send_message,
            bg='#4CAF50',
            fg='white',
            font=('Arial', 12, 'bold')
        )
        self.send_button.pack(side=tk.RIGHT)
        
        # Status and buttons frame
        bottom_frame = tk.Frame(main_frame, bg='#2b2b2b')
        bottom_frame.pack(fill=tk.X)
        
        # Status label
        self.status_label = tk.Label(
            bottom_frame, 
            text="Ready", 
            bg='#2b2b2b', 
            fg='#00ff00',
            font=('Arial', 10)
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Buttons
        buttons_frame = tk.Frame(bottom_frame, bg='#2b2b2b')
        buttons_frame.pack(side=tk.RIGHT)
        
        tk.Button(buttons_frame, text="💾 Save", command=self.save_chat,
                 bg='#FF9800', fg='white', font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
        
        tk.Button(buttons_frame, text="🧠 Memory", command=self.view_memory,
                 bg='#9C27B0', fg='white', font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
        
        tk.Button(buttons_frame, text="🗑️ Clear", command=self.clear_chat,
                 bg='#F44336', fg='white', font=('Arial', 9)).pack(side=tk.LEFT, padx=2)
        
        # Welcome message
        self.add_to_chat("🤖 Assistant", 
            "Hello! I'm your Jan assistant with tools. I can:\n\n" +
            "📁 Read and write files (try: 'write hello to test.txt')\n" +
            "🧠 Remember things (try: 'remember my name is John')\n" +
            "💻 Run commands (try: 'run the command ls')\n" +
            "🔍 Search web (placeholder)\n\n" +
            "What would you like me to help you with?")
        
        self.user_input.focus()
    
    def add_to_chat(self, sender, message):
        """Add message to chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding
        if sender == "You":
            color = "#00ff00"
        elif sender == "🤖 Assistant":
            color = "#87CEEB"
        elif sender == "🔧 Tool":
            color = "#FFA500"
        else:
            color = "#ffffff"
        
        # Insert with colors (simplified)
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}:\n{message}\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def update_status(self, status, color="#00ff00"):
        """Update status label"""
        self.status_label.config(text=status, fg=color)
        self.root.update()
    
    def send_message(self, event=None):
        """Send message to assistant"""
        message = self.user_input.get().strip()
        if not message:
            return
            
        self.user_input.delete(0, tk.END)
        self.add_to_chat("You", message)
        
        self.send_button.config(state=tk.DISABLED)
        self.update_status("🤔 Thinking...", "#ffff00")
        
        # Process in thread
        threading.Thread(target=self.process_message, args=(message,), daemon=True).start()
    
    def process_message(self, message):
        """Process message with tools"""
        try:
            response = self.chat_with_tools(message)
            self.root.after(0, lambda: self.add_to_chat("🤖 Assistant", response))
            self.root.after(0, lambda: self.update_status("Ready", "#00ff00"))
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, lambda: self.add_to_chat("🤖 Assistant", error_msg))
            self.root.after(0, lambda: self.update_status("Error", "#ff0000"))
            self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
    
    def chat_with_tools(self, message):
        """Chat with tools available"""
        system_message = """You are a helpful assistant with access to tools. When the user asks you to:
- READ a file: respond with "TOOL_READ_FILE: filename"
- WRITE to a file: respond with "TOOL_WRITE_FILE: filename|content"
- REMEMBER something: respond with "TOOL_REMEMBER: key|value"
- RECALL something: respond with "TOOL_RECALL: key"
- RUN a command: respond with "TOOL_COMMAND: command"

After using a tool, I'll give you the result and you can respond normally to the user."""
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": message}
        ]
        
        response = self.call_api(messages)
        
        # Check for tools
        if "TOOL_" in response:
            self.root.after(0, lambda: self.update_status("🔧 Using tools...", "#FFA500"))
            tool_result = self.handle_tool_call(response)
            self.root.after(0, lambda: self.add_to_chat("🔧 Tool", tool_result))
            
            # Get final response
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": f"Tool result: {tool_result}. Please respond to the user."})
            final_response = self.call_api(messages)
            return final_response
        else:
            return response
    
    def call_api(self, messages):
        """Make API call to Jan"""
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Error: {response.text}"
    
    def handle_tool_call(self, response):
        """Handle tool calls"""
        if "TOOL_READ_FILE:" in response:
            filename = response.split("TOOL_READ_FILE:")[1].strip()
            return self.read_file(filename)
        elif "TOOL_WRITE_FILE:" in response:
            parts = response.split("TOOL_WRITE_FILE:")[1].strip().split("|", 1)
            filename = parts[0].strip()
            content = parts[1].strip() if len(parts) > 1 else ""
            return self.write_file(filename, content)
        elif "TOOL_REMEMBER:" in response:
            parts = response.split("TOOL_REMEMBER:")[1].strip().split("|", 1)
            key = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""
            return self.remember(key, value)
        elif "TOOL_RECALL:" in response:
            key = response.split("TOOL_RECALL:")[1].strip()
            return self.recall(key)
        elif "TOOL_COMMAND:" in response:
            command = response.split("TOOL_COMMAND:")[1].strip()
            return self.run_command(command)
        return "Tool not recognized"
    
    def read_file(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"File '{filename}' contents:\n{content}"
        except Exception as e:
            return f"Error reading file '{filename}': {str(e)}"
    
    def write_file(self, filename, content):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to file '{filename}'"
        except Exception as e:
            return f"Error writing to file '{filename}': {str(e)}"
    
    def remember(self, key, value):
        self.memory[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat()
        }
        self.save_memory()
        return f"Remembered: {key} = {value}"
    
    def recall(self, key):
    # Try exact match first
    if key in self.memory:
        item = self.memory[key]
        return f"Recalled: {key} = {item['value']} (stored on {item['timestamp']})"
    
    # Try fuzzy matching for common variations
    key_lower = key.lower().strip()
    for stored_key in self.memory:
        if key_lower in stored_key.lower() or stored_key.lower() in key_lower:
            item = self.memory[stored_key]
            return f"Recalled: {stored_key} = {item['value']} (stored on {item['timestamp']})"
    
    return f"No memory found for key: {key}. Available memories: {list(self.memory.keys())}"
    
    def run_command(self, command):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return f"Command output:\n{result.stdout}"
            else:
                return f"Command error:\n{result.stderr}"
        except Exception as e:
            return f"Error running command: {str(e)}"
    
    def save_chat(self):
        """Save chat history"""
        filename = filedialog.asksaveasfilename(
            title="Save chat history",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                content = self.chat_display.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Chat saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def view_memory(self):
        """Show memory contents"""
        memory_window = tk.Toplevel(self.root)
        memory_window.title("🧠 Memory")
        memory_window.geometry("400x300")
        
        text_widget = tk.Text(memory_window)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        if self.memory:
            for key, item in self.memory.items():
                text_widget.insert(tk.END, f"🔑 {key}: {item['value']}\n📅 {item['timestamp']}\n\n")
        else:
            text_widget.insert(tk.END, "No memories stored yet.")
        
        text_widget.config(state=tk.DISABLED)
    
    def clear_chat(self):
        """Clear chat"""
        if messagebox.askyesno("Clear", "Clear chat history?"):
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.add_to_chat("🤖 Assistant", "Chat cleared! How can I help?")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = JanAssistantGUI()
    app.run()
