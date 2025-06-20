import tkinter as tk

import requests
from src.core.logging_config import get_logger, setup_logging


class SimpleJanGUI:
    def __init__(self):
        self.api_base = "http://127.0.0.1:1337/v1"
        self.api_key = "124578"
        self.model = "qwen3:30b-a3b"
        setup_logging()
        self.logger = get_logger(self.__class__.__name__)
        self.setup_gui()

    def setup_gui(self):
        self.logger.info("Creating simple GUI")

        self.root = tk.Tk()
        self.root.title("Jan Assistant")
        self.root.geometry("600x400")

        # Simple text widget instead of ScrolledText
        self.logger.info("Creating text area")
        self.text_area = tk.Text(self.root, height=20, width=70)
        self.text_area.pack(padx=10, pady=10)

        # Input frame
        self.logger.info("Creating input frame")
        input_frame = tk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        # Entry widget
        self.logger.info("Creating entry")
        self.entry = tk.Entry(input_frame, font=("Arial", 12))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entry.bind("<Return>", self.send_message)

        # Send button
        self.logger.info("Creating button")
        tk.Button(input_frame, text="Send", command=self.send_message).pack(
            side=tk.RIGHT
        )

        # Welcome message
        self.logger.info("Adding welcome")
        self.add_message(
            "System", "Simple Jan GUI loaded! Type a message and press Enter."
        )

        self.logger.info("Simple GUI ready")

    def add_message(self, sender, message):
        """Add message to display"""
        self.text_area.insert(tk.END, f"{sender}: {message}\n\n")
        self.text_area.see(tk.END)

    def send_message(self, event=None):
        """Send message"""
        message = self.entry.get().strip()
        if not message:
            return

        self.entry.delete(0, tk.END)
        self.add_message("You", message)

        # Test with simple response first
        if message.lower() == "test":
            self.add_message("Assistant", "Test successful! GUI is working.")
        elif message.lower() == "api":
            # Test API call
            try:
                response = self.call_jan_api(message)
                self.add_message("Assistant", response)
            except Exception as e:
                self.add_message("Error", str(e))
        else:
            self.add_message(
                "Assistant",
                f"You said: {message}. Type 'test' or 'api' to test features.",
            )

    def call_jan_api(self, message):
        """Simple API call"""
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": message}],
            "stream": False,
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"API Error: {response.text}"

    def run(self):
        self.logger.info("Starting simple mainloop")
        self.root.mainloop()


if __name__ == "__main__":
    app = SimpleJanGUI()
    app.run()
