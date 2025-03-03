# main.py
import tkinter as tk # using tkinter for the GUI, could be replcaed with custumTKinter, or a web interface
from frontend.app_gui import DatabaseComparisonApp
from backend.db_manager import setup_logging

def main():
    # Set up logging
    setup_logging()
    
    # Initialize the main application
    root = tk.Tk()
    app = DatabaseComparisonApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()