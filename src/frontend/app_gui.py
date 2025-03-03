# frontend/app_gui.py
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import sys
import logging
import threading
from backend.db_comparer import SQLiteComparer
from backend.report_generator import ReportGenerator

# Add parent directory to path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

class DatabaseComparisonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SQLite Database Comparison Utility")
        self.root.geometry("800x600")
        
        self.comparer = SQLiteComparer()
        
        # Status variables
        self.is_comparing = False
        
        self.create_widgets()
        logger.info("GUI initialized")
    
    def create_widgets(self):
        # Create menu
        self.create_menu()
        
        # Top frame for database selection
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        # Database 1 selection
        ttk.Label(top_frame, text="Database 1:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.db1_path_var = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.db1_path_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(top_frame, text="Browse...", command=self.browse_db1).grid(row=0, column=2, padx=5, pady=5)
        
        # Database 2 selection
        ttk.Label(top_frame, text="Database 2:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.db2_path_var = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.db2_path_var, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(top_frame, text="Browse...", command=self.browse_db2).grid(row=1, column=2, padx=5, pady=5)
        
        # Compare button
        self.compare_btn = ttk.Button(top_frame, text="Compare Databases", command=self.start_comparison)
        self.compare_btn.grid(row=2, column=0, columnspan=3, pady=10)
        
        # Middle frame for summary results
        mid_frame = ttk.LabelFrame(self.root, text="Comparison Summary", padding="10")
        mid_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Summary labels
        ttk.Label(mid_frame, text="Overall Difference Score:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.diff_score_var = tk.StringVar(value="--")
        ttk.Label(mid_frame, textvariable=self.diff_score_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(mid_frame, text="Similarity Score:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.similarity_score_var = tk.StringVar(value="--")
        ttk.Label(mid_frame, textvariable=self.similarity_score_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=780, mode='determinate', variable=self.progress_var)
        self.progress.pack(padx=10, pady=5)
        
        # Bottom frame for detailed report
        bottom_frame = ttk.LabelFrame(self.root, text="Detailed Report", padding="10")
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Text widget for the report
        self.report_text = tk.Text(bottom_frame, wrap=tk.WORD, width=80, height=20)
        self.report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for the text widget
        scrollbar = ttk.Scrollbar(bottom_frame, orient=tk.VERTICAL, command=self.report_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.report_text.configure(yscrollcommand=scrollbar.set)
        
        # Export button
        self.export_btn = ttk.Button(self.root, text="Export Report", command=self.export_report)
        self.export_btn.pack(pady=10)
        self.export_btn.config(state=tk.DISABLED)
    
    def create_menu(self):
        """Create the main menu."""
        menu_bar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Open Database 1...", command=self.browse_db1)
        file_menu.add_command(label="Open Database 2...", command=self.browse_db2)
        file_menu.add_separator()
        file_menu.add_command(label="Export Report...", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Actions menu
        action_menu = tk.Menu(menu_bar, tearoff=0)
        action_menu.add_command(label="Compare Databases", command=self.start_comparison)
        action_menu.add_command(label="Clear Results", command=self.clear_results)
        menu_bar.add_cascade(label="Actions", menu=action_menu)
        
        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Help", command=self.show_help)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menu_bar)
    
    def browse_db1(self):
        """Open file dialog to select first database."""
        filename = filedialog.askopenfilename(
            title="Select first SQLite database",
            filetypes=[("SQLite Database", "*.db;*.sqlite;*.sqlite3;*.db3"), ("All files", "*.*")]
        )
        if filename:
            self.db1_path_var.set(filename)
            logger.info(f"Selected database 1: {filename}")
    
    def browse_db2(self):
        """Open file dialog to select second database."""
        filename = filedialog.askopenfilename(
            title="Select second SQLite database",
            filetypes=[("SQLite Database", "*.db;*.sqlite;*.sqlite3;*.db3"), ("All files", "*.*")]
        )
        if filename:
            self.db2_path_var.set(filename)
            logger.info(f"Selected database 2: {filename}")
    
    def update_progress(self, value, status=None):
        """Update progress bar and status bar."""
        self.progress_var.set(value)
        if status:
            self.status_var.set(status)
        self.root.update_idletasks()
    
    def start_comparison(self):
        """Start the comparison process in a separate thread."""
        db1_path = self.db1_path_var.get()
        db2_path = self.db2_path_var.get()
        
        if not db1_path or not db2_path:
            messagebox.showerror("Error", "Please select both databases")
            return
        
        if self.is_comparing:
            messagebox.showinfo("Info", "Comparison already in progress")
            return
        
        # Disable controls during comparison
        self.is_comparing = True
        self.compare_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.DISABLED)
        
        # Clear previous results
        self.clear_results()
        
        # Start comparison in a separate thread
        self.update_progress(0, "Starting comparison...")
        comparison_thread = threading.Thread(target=self.run_comparison, args=(db1_path, db2_path))
        comparison_thread.daemon = True
        comparison_thread.start()
    
    def run_comparison(self, db1_path, db2_path):
        """Run the database comparison in a background thread."""
        try:
            # Connect to databases
            self.update_progress(10, "Connecting to databases...")
            if not self.comparer.connect_databases(db1_path, db2_path):
                self.handle_error("Failed to connect to one or both databases")
                return
            
            self.update_progress(30, "Analyzing database structures...")
            
            # Compare databases
            self.comparer.compare_databases()
            self.update_progress(90, "Generating report...")
            
            # Update results in the main thread
            self.root.after(0, self.update_results)
            
        except Exception as e:
            error_message = f"An error occurred during comparison: {str(e)}"
            logger.error(error_message, exc_info=True)
            # Capture the error message outside the lambda
            self.root.after(0, lambda msg=error_message: self.handle_error(msg))
    
    def update_results(self):
        """Update the UI with comparison results."""
        try:
            # Update score displays
            diff_score = self.comparer.differences["overall_diff_score"]
            similarity = self.comparer.similarity_score
            
            self.diff_score_var.set(f"{diff_score:.4f} (0=identical, 1=completely different)")
            self.similarity_score_var.set(f"{similarity:.4f} (1=identical, 0=completely different)")
            
            # Generate and display detailed report
            report = ReportGenerator.generate_detailed_report(self.comparer)
            self.report_text.delete(1.0, tk.END)
            self.report_text.insert(tk.END, report)
            
            # Enable export button
            self.export_btn.config(state=tk.NORMAL)
            
            # Update progress and status
            self.update_progress(100, "Comparison complete")
            
        except Exception as e:
            logger.error(f"Error updating results: {str(e)}", exc_info=True)
            self.handle_error(f"Error updating results: {str(e)}")
        finally:
            # Close connections
            self.comparer.close_connections()
            
            # Re-enable controls
            self.compare_btn.config(state=tk.NORMAL)
            self.is_comparing = False
    
    def handle_error(self, message):
        """Display error message and reset UI."""
        messagebox.showerror("Error", message)
        self.status_var.set("Error occurred")
        self.progress_var.set(0)
        self.compare_btn.config(state=tk.NORMAL)
        self.is_comparing = False
    
    def export_report(self):
        """Export the comparison report to a file."""
        if not hasattr(self.comparer, 'differences') or not self.comparer.differences:
            messagebox.showinfo("Info", "No comparison results to export")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            report = ReportGenerator.generate_detailed_report(self.comparer)
            success = ReportGenerator.save_report_to_file(report, filename)
            
            if success:
                messagebox.showinfo("Success", f"Report successfully saved to {filename}")
            # Error handling is already done in the ReportGenerator class
    
    def clear_results(self):
        """Clear all comparison results."""
        self.report_text.delete(1.0, tk.END)
        self.diff_score_var.set("--")
        self.similarity_score_var.set("--")
        self.progress_var.set(0)
        self.status_var.set("Ready")
        self.export_btn.config(state=tk.DISABLED)
        logger.info("Results cleared")
    
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "SQLite Database Comparison Utility\n\n"
            "A tool for comparing the structure and content of SQLite databases.\n\n"
            "Version 1.0"
        )
    
    def show_help(self):
        """Show help dialog."""
        help_text = """SQLite Database Comparison Utility Help
        
        How to use this utility:

        1. Select the first database using the 'Database 1' browse button
        2. Select the second database using the 'Database 2' browse button
        3. Click 'Compare Databases' to start the comparison process
        4. View the summary and detailed report
        5. Export the report to a file if needed

        The comparison analyzes both structure and content differences, including:
        - Schema differences (tables, columns, indexes, constraints)
        - Data differences (row counts, sample data comparisons)
        - Overall similarity score

        For support or feedback, please contact support@dbcompare.example.com
        """
    
        # Create a dialog with scrollable text
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("Help")
        help_dialog.geometry("600x400")
        help_dialog.resizable(True, True)
        
        # Add text widget with scrollbar
        help_text_widget = tk.Text(help_dialog, wrap=tk.WORD, padx=10, pady=10)
        help_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(help_dialog, orient=tk.VERTICAL, command=help_text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        help_text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Insert help text
        help_text_widget.insert(tk.END, help_text)
        help_text_widget.config(state=tk.DISABLED)  # Make it read-only