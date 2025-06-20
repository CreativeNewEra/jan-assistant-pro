#!/usr/bin/env python3
"""
Jan Assistant Pro
A powerful local-first AI assistant with tools
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from gui.main_window import JanAssistantGUI
    from core.config import Config
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

def main():
    """Main application entry point"""
    try:
        # Load configuration
        config = Config()
        
        # Create and run GUI
        app = JanAssistantGUI(config)
        app.run()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {str(e)}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
