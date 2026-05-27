import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess

class OfflineAIDesktopAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("Offline AI Desktop Assistant")
        self.root.geometry("800x600")

        # Create text area for logging daily activities
        self.text_area = tk.Text(self.root, height=20, width=80)
        self.text_area.pack(pady=10)

        # Create frame for buttons
        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack()

        # Create 'Generate Report' button
        self.generate_report_button = tk.Button(self.button_frame, text="Generate Report", command=self.generate_report)
        self.generate_report_button.pack(side=tk.LEFT, padx=10)

        # Create 'Save to File' button
        self.save_to_file_button = tk.Button(self.button_frame, text="Save to File", command=self.save_to_file)
        self.save_to_file_button.pack(side=tk.LEFT, padx=10)

        # Create label to display report
        self.report_label = tk.Label(self.root, text="Generated Report:")
        self.report_label.pack(pady=10)

        # Create text area to display report
        self.report_text_area = tk.Text(self.root, height=10, width=80)
        self.report_text_area.pack()

    def generate_report(self):
        # Get text from text area
        text = self.text_area.get("1.0", tk.END)

        # Use subprocess to call Ollama
        try:
            output = subprocess.check_output(["ollama", "run", "llama3", "--prompt", text], text=True)
            report = output.strip()
        except FileNotFoundError:
            messagebox.showerror("Error", "Ollama not found. Please install Ollama locally.")
            return
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")
            return

        # Display report in report text area
        self.report_text_area.delete("1.0", tk.END)
        self.report_text_area.insert("1.0", report)

    def save_to_file(self):
        # Get report from report text area
        report = self.report_text_area.get("1.0", tk.END)

        # Open file dialog to save report
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text File", "*.txt")])

        if file_path:
            # Save report to file
            with open(file_path, "w") as f:
                f.write(report)

if __name__ == "__main__":
    root = tk.Tk()
    app = OfflineAIDesktopAssistant(root)
    root.mainloop()