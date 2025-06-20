"""
Main GUI window for Jan Assistant Pro
Refactored from the original working implementation
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime
import threading
from typing import Dict, Any

# Import our core modules
from core.config import Config
from core.app_controller import AppController


class JanAssistantGUI:
    """Main GUI application for Jan Assistant Pro"""

    def __init__(self, config: Config):
        self.config = config
        self.controller = AppController(config)
        
        # Setup GUI
        self.setup_gui()
    
    def setup_gui(self):
        """Create the GUI interface"""
        self.root = tk.Tk()
        self.root.title("🤖 Jan Assistant Pro")
        self.root.geometry(self.config.window_size)
        
        # Apply theme
        if self.config.theme == "dark":
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
        
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="🤖 Jan Assistant Pro", 
            font=('Arial', 16, 'bold'), 
            bg=self.bg_color, 
            fg=self.fg_color
        )
        title_label.pack(pady=(0, 10))
        
        # Chat display frame with scrollbar
        chat_frame = tk.Frame(main_frame, bg=self.bg_color)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Text widget with manual scrollbar
        self.chat_display = tk.Text(
            chat_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            bg=self.chat_bg_color,
            fg=self.fg_color,
            font=(self.config.get('ui.font_family', 'Consolas'), 
                  self.config.get('ui.font_size', 10)),
            state=tk.DISABLED
        )
        
        # Manual scrollbar
        scrollbar = tk.Scrollbar(chat_frame, command=self.chat_display.yview)
        self.chat_display.config(yscrollcommand=scrollbar.set)
        
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Input frame
        input_frame = tk.Frame(main_frame, bg=self.bg_color)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # User input
        self.user_input = tk.Entry(
            input_frame, 
            font=('Arial', 12),
            bg=self.input_bg_color,
            fg=self.fg_color,
            insertbackground=self.fg_color
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
        bottom_frame = tk.Frame(main_frame, bg=self.bg_color)
        bottom_frame.pack(fill=tk.X)
        
        # Status label
        self.status_label = tk.Label(
            bottom_frame, 
            text="Ready", 
            bg=self.bg_color, 
            fg='#00ff00',
            font=('Arial', 10)
        )
        self.status_label.pack(side=tk.LEFT)
        
        # Buttons
        self._create_buttons(bottom_frame)
        
        # Welcome message
        self.add_to_chat("🤖 Assistant", self._get_welcome_message())
        
        # Test API connection
        self._test_api_connection()
        
        self.user_input.focus()
    
    def _apply_dark_theme(self):
        """Apply dark theme colors"""
        self.bg_color = '#2b2b2b'
        self.fg_color = '#ffffff'
        self.chat_bg_color = '#1e1e1e'
        self.input_bg_color = '#3c3c3c'
        self.root.configure(bg=self.bg_color)
    
    def _apply_light_theme(self):
        """Apply light theme colors"""
        self.bg_color = '#ffffff'
        self.fg_color = '#000000'
        self.chat_bg_color = '#f5f5f5'
        self.input_bg_color = '#ffffff'
        self.root.configure(bg=self.bg_color)
    
    def _create_buttons(self, parent):
        """Create action buttons"""
        buttons_frame = tk.Frame(parent, bg=self.bg_color)
        buttons_frame.pack(side=tk.RIGHT)
        
        buttons = [
            ("💾 Save", self.save_chat, '#FF9800'),
            ("🧠 Memory", self.view_memory, '#9C27B0'),
            ("⚙️ Settings", self.show_settings, '#607D8B'),
            ("🔧 Test API", self.test_api, '#2196F3'),
            ("🗑️ Clear", self.clear_chat, '#F44336'),
        ]
        
        for text, command, color in buttons:
            tk.Button(
                buttons_frame, 
                text=text, 
                command=command,
                bg=color, 
                fg='white', 
                font=('Arial', 9)
            ).pack(side=tk.LEFT, padx=2)
    
    def _get_welcome_message(self) -> str:
        """Get welcome message"""
        return self.controller.get_welcome_message()
    
    def _test_api_connection(self):
        """Test API connection on startup"""
        def test():
            status = self.controller.test_api_connection()
            if status['connected']:
                self.root.after(0, lambda: self.update_status("✅ Connected", "#00ff00"))
            else:
                error_msg = status.get('error', 'Unknown error')
                self.root.after(0, lambda: self.update_status(f"❌ {error_msg}", "#ff0000"))
        
        threading.Thread(target=test, daemon=True).start()
    
    def add_to_chat(self, sender: str, message: str):
        """Add message to chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on sender
        if sender == "You":
            color = "#00ff00"
        elif sender == "🤖 Assistant":
            color = "#87CEEB"
        elif sender == "🔧 Tool":
            color = "#FFA500"
        elif sender == "⚠️ Error":
            color = "#ff6b6b"
        else:
            color = self.fg_color
        
        # Insert message
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}:\n{message}\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def update_status(self, status: str, color: str = "#00ff00"):
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
    
    def process_message(self, message: str):
        """Process message with the controller"""
        response = self.controller.process_message(message)
        
        if response['type'] == 'error':
            self.root.after(0, lambda: self.add_to_chat("⚠️ Error", response['content']))
        else:
            self.root.after(0, lambda: self.add_to_chat("🤖 Assistant", response['content']))

        self.root.after(0, lambda: self.update_status("Ready", "#00ff00"))
        self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))

    # GUI Event handlers
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
        memory_window.title("🧠 Memory Manager")
        memory_window.geometry("600x400")
        memory_window.configure(bg=self.bg_color)
        
        # Create notebook-style tabs
        notebook_frame = tk.Frame(memory_window, bg=self.bg_color)
        notebook_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Memory content
        text_widget = tk.Text(
            notebook_frame, 
            bg=self.chat_bg_color, 
            fg=self.fg_color,
            font=('Consolas', 10)
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Load memories
        memories = self.controller.memory_manager.list_memories()
        if memories:
            for key, memory in memories:
                text_widget.insert(tk.END, f"🔑 {key}\n")
                text_widget.insert(tk.END, f"   📝 {memory['value']}\n")
                text_widget.insert(tk.END, f"   📁 Category: {memory.get('category', 'general')}\n")
                text_widget.insert(tk.END, f"   📅 {memory['timestamp']}\n\n")
        else:
            text_widget.insert(tk.END, "No memories stored yet.")
        
        text_widget.config(state=tk.DISABLED)
    
    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ Settings")
        settings_window.geometry("500x400")
        settings_window.configure(bg=self.bg_color)
        
        # Settings content
        tk.Label(settings_window, text="⚙️ Settings", 
                font=('Arial', 14, 'bold'), 
                bg=self.bg_color, fg=self.fg_color).pack(pady=10)
        
        # API settings
        api_frame = tk.LabelFrame(settings_window, text="API Configuration", 
                                 bg=self.bg_color, fg=self.fg_color)
        api_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(api_frame, text=f"URL: {self.controller.config.api_base_url}", 
                bg=self.bg_color, fg=self.fg_color).pack(anchor=tk.W)
        tk.Label(api_frame, text=f"Model: {self.controller.config.model_name}", 
                bg=self.bg_color, fg=self.fg_color).pack(anchor=tk.W)
        
        # Memory settings
        memory_frame = tk.LabelFrame(settings_window, text="Memory", 
                                    bg=self.bg_color, fg=self.fg_color)
        memory_frame.pack(fill=tk.X, padx=10, pady=5)
        
        stats = self.controller.memory_manager.get_stats()
        tk.Label(memory_frame, text=f"Total memories: {stats['total_entries']}", 
                bg=self.bg_color, fg=self.fg_color).pack(anchor=tk.W)
        tk.Label(memory_frame, text=f"Categories: {', '.join(stats['categories'])}", 
                bg=self.bg_color, fg=self.fg_color).pack(anchor=tk.W)
    
    def test_api(self):
        """Test API connection"""
        def test():
            self.root.after(0, lambda: self.update_status("🔄 Testing API...", "#ffff00"))
            status = self.controller.test_api_connection()
            
            if status['connected']:
                msg = f"✅ Connected! Latency: {status.get('latency_ms', 'N/A')}ms"
                self.root.after(0, lambda: self.update_status(msg, "#00ff00"))
                self.root.after(0, lambda: self.add_to_chat("System", f"API test successful. {msg}"))
            else:
                error = status.get('error', 'Unknown error')
                self.root.after(0, lambda: self.update_status(f"❌ Failed", "#ff0000"))
                self.root.after(0, lambda: self.add_to_chat("System", f"API test failed: {error}"))
        
        threading.Thread(target=test, daemon=True).start()
    
    def clear_chat(self):
        """Clear chat"""
        if messagebox.askyesno("Clear Chat", "Clear chat history?"):
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)
            self.controller.conversation_history = []
            self.add_to_chat("🤖 Assistant", "Chat cleared! How can I help?")
    
    def run(self):
        """Start the GUI main loop"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("Application interrupted")
        finally:
            # Save memory on exit
            self.controller.memory_manager.save_memory()
