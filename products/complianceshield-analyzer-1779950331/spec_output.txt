# NETWORK POLICY: No external network calls.
# Ollama subprocess is localhost-only.

# Requirements
#   - Python 3.9+
#   - Tkinter (ships with CPython)
#   - Ollama endpoint (http://localhost:11434)
#   - sqlite3 (ships with CPython)
#   - No external dependencies beyond those shipped with CPython

# PRODUCT NAME: ComplianceShield Analyzer
# BUILD SUMMARY: ComplianceShield Analyzer is a desktop application that automates the review and analysis of financial transactions to ensure compliance with anti-money laundering (AML) and know-your-customer (KYC) regulations. The application uses local AI to analyze transactions and identify high-risk transactions, reducing the manual labor required for compliance analysis.

# OLLAMA MODEL RECOMMENDATION:
#   Primary: llama3 (recommended for its reasoning capabilities, which are well-suited for AML/KYC analysis)
#   Fallback: codellama (recommended as a fallback for its code audit capabilities, which can be used for AML/KYC analysis when the primary model is unavailable)

import os
import tkinter as tk
from tkinter import ttk, filedialog
from queue import Queue
import threading
import http.client
import hashlib
import sqlite3
import re
import json
import csv
import time

# PII filter
def pii_filter(text):
    """Redact PII from text"""
    pii_pattern = r"(?:\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b)|(?:\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b)|(?:\b\d{16}\b)|(?:\b[A-Za-z0-9/_+=]+\.pem\b)|(?:\b[A-Za-z0-9/_+=]+\.jwt\b)|(?:\b[A-Za-z0-9/_+=]+\.api\b)|(?:\b[0-9]{9,12}\b)"
    text = re.sub(pii_pattern, "REDACTED", text)
    return text

# Audit logger
def audit_logger(action_type, file_hash, outcome):
    """Log action to audit.db"""
    conn = sqlite3.connect("audit.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS audit (timestamp TEXT, action_type TEXT, file_hash TEXT, outcome TEXT)")
    c.execute("INSERT INTO audit VALUES (CURRENT_TIMESTAMP, ?, ?, ?)", (action_type, file_hash, outcome))
    conn.commit()
    conn.close()

# Ollama interface
class OllamaInterface:
    def __init__(self, model_name, timeout=120):
        self.model_name = model_name
        self.timeout = timeout

    def query(self, prompt):
        """Query Ollama model"""
        conn = http.client.HTTPConnection("localhost", 11434)
        conn.request("POST", f"/{self.model_name}", json.dumps({"prompt": pii_filter(prompt)}).encode(), {"Content-Type": "application/json"})
        response = conn.getresponse()
        if response.status == 200:
            return response.read().decode()
        else:
            return None

# FEATURE 1: File loading
def load_file():
    """Load file into application"""
    filename = filedialog.askopenfilename()
    if filename:
        file_hash = hashlib.sha256(open(filename, "rb").read()).hexdigest()
        audit_logger("file_load", file_hash, "success")
        return filename, file_hash

# FEATURE 2: Configuration saving
def save_config(model_name, pii_redaction, output_format, timeout):
    """Save configuration"""
    config = {
        "model_name": model_name,
        "pii_redaction": pii_redaction,
        "output_format": output_format,
        "timeout": timeout
    }
    with open("config.json", "w") as f:
        json.dump(config, f)

# FEATURE 3: AI analysis
def analyze_file(filename):
    """Analyze file using Ollama model"""
    if not os.path.exists("config.json"):
        return "Error: No configuration file found"
    with open("config.json", "r") as f:
        config = json.load(f)
    model_name = config["model_name"]
    pii_redaction = config["pii_redaction"]
    output_format = config["output_format"]
    timeout = config["timeout"]
    ollama = OllamaInterface(model_name, timeout)
    prompt = open(filename, "r").read()
    if pii_redaction:
        prompt = pii_filter(prompt)
    result = ollama.query(prompt)
    if result:
        if output_format == "JSON":
            return json.loads(result)
        elif output_format == "CSV":
            return csv.reader(result.splitlines())
        else:
            return result
    else:
        return "Error: Ollama query failed"

# FEATURE 4: Export results
def export_results(filename, results):
    """Export results to file"""
    if isinstance(results, dict):
        with open(filename, "w") as f:
            json.dump(results, f)
    elif isinstance(results, csv.reader):
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(results)
    else:
        with open(filename, "w") as f:
            f.write(results)

# FEATURE 5: Clear queue
def clear_queue(queue):
    """Clear queue"""
    queue.clear()

class TkinterApp:
    def __init__(self, root):
        self.root = root
        self.queue = Queue()
        self.model_name = tk.StringVar(value="llama3")
        self.pii_redaction = tk.BooleanVar(value=True)
        self.output_format = tk.StringVar(value="JSON")
        self.timeout = tk.IntVar(value=120)

        # Panel 1: Input / File Loading Zone
        self.panel1 = tk.Frame(self.root)
        self.panel1.pack(fill="x")
        self.browse_button = tk.Button(self.panel1, text="Browse Files", command=self.browse_files)
        self.browse_button.pack(side="left")
        self.clear_button = tk.Button(self.panel1, text="Clear Queue", command=self.clear_queue)
        self.clear_button.pack(side="left")
        self.file_listbox = tk.Listbox(self.panel1)
        self.file_listbox.pack(side="left", fill="both", expand=True)

        # Panel 2: Configuration Panel
        self.panel2 = tk.Frame(self.root)
        self.panel2.pack(fill="x")
        self.model_label = tk.Label(self.panel2, text="Ollama Model:")
        self.model_label.pack(side="left")
        self.model_option = tk.OptionMenu(self.panel2, self.model_name, "llama3", "codellama", "mistral")
        self.model_option.pack(side="left")
        self.pii_label = tk.Label(self.panel2, text="PII Redaction:")
        self.pii_label.pack(side="left")
        self.pii_checkbox = tk.Checkbutton(self.panel2, variable=self.pii_redaction)
        self.pii_checkbox.pack(side="left")
        self.output_label = tk.Label(self.panel2, text="Output Format:")
        self.output_label.pack(side="left")
        self.output_option = tk.OptionMenu(self.panel2, self.output_format, "JSON", "CSV", "plain text")
        self.output_option.pack(side="left")
        self.timeout_label = tk.Label(self.panel2, text="Timeout:")
        self.timeout_label.pack(side="left")
        self.timeout_slider = tk.Scale(self.panel2, from_=30, to=300, orient="horizontal", variable=self.timeout)
        self.timeout_slider.pack(side="left")

        # Panel 3: Live Processing Log
        self.panel3 = tk.Frame(self.root)
        self.panel3.pack(fill="both", expand=True)
        self.log_text = tk.Text(self.panel3)
        self.log_text.pack(fill="both", expand=True)

        # Panel 4: Results / Output Viewer
        self.panel4 = tk.Frame(self.root)
        self.panel4.pack(fill="x")
        self.copy_button = tk.Button(self.panel4, text="Copy to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.pack(side="left")
        self.export_button = tk.Button(self.panel4, text="Export", command=self.export)
        self.export_button.pack(side="left")
        self.clear_button = tk.Button(self.panel4, text="Clear", command=self.clear)
        self.clear_button.pack(side="left")

        # Status Bar
        self.status_bar = tk.Label(self.root, text="Ready")
        self.status_bar.pack(fill="x")

        # Menu Bar
        self.menu_bar = tk.Menu(self.root)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open", command=self.browse_files)
        self.file_menu.add_command(label="Save", command=self.save_config)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.settings_menu.add_command(label="Settings", command=self.save_config)
        self.menu_bar.add_cascade(label="Settings", menu=self.settings_menu)
        self.audit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.audit_menu.add_command(label="View Audit Log", command=self.view_audit_log)
        self.menu_bar.add_cascade(label="Audit", menu=self.audit_menu)
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Help", command=self.view_help)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        self.root.config(menu=self.menu_bar)

        # Start background thread for Ollama queries
        self.background_thread = threading.Thread(target=self.background_task)
        self.background_thread.start()

    def browse_files(self):
        """Browse files and add to queue"""
        filename, file_hash = load_file()
        self.file_listbox.insert("end", filename)
        self.queue.put((filename, file_hash))

    def save_config(self):
        """Save configuration"""
        save_config(self.model_name.get(), self.pii_redaction.get(), self.output_format.get(), self.timeout.get())

    def copy_to_clipboard(self):
        """Copy results to clipboard"""
        # Not implemented

    def export(self):
        """Export results"""
        # Not implemented

    def clear(self):
        """Clear results"""
        # Not implemented

    def view_audit_log(self):
        """View audit log"""
        # Not implemented

    def view_help(self):
        """View help"""
        # Not implemented

    def background_task(self):
        """Run Ollama queries in background"""
        while True:
            if not self.queue.empty():
                filename, file_hash = self.queue.get()
                result = analyze_file(filename)
                self.log_text.insert("end", f"Analyzing {filename}...\n")
                if result:
                    self.log_text.insert("end", f"Result: {result}\n")
                else:
                    self.log_text.insert("end", f"Error: Ollama query failed\n")
            time.sleep(1)

def main():
    root = tk.Tk()
    app = TkinterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

# FEATURE SPECIFICATIONS:
#   FEATURE 1: File loading, Trigger: Browse Files button, Input: file path, Processing Logic: load file into application, Output: file path and hash, Audit Entry: file load
#   FEATURE 2: Configuration saving, Trigger: Save Config button, Input: model name, PII redaction, output format, and timeout, Processing Logic: save configuration to file, Output: None, Audit Entry: config save
#   FEATURE 3: AI analysis, Trigger: Analyze button, Input: file path, Processing Logic: analyze file using Ollama model, Output: analysis result, Audit Entry: file analysis
#   FEATURE 4: Export results, Trigger: Export button, Input: result, Processing Logic: export result to file, Output: exported file, Audit Entry: result export
#   FEATURE 5: Clear queue, Trigger: Clear Queue button, Input: None, Processing Logic: clear queue, Output: None, Audit Entry: queue clear

# DEPLOYMENT NOTES:
#   - Python version: 3.9+
#   - Ollama setup command: Run Ollama endpoint using http://localhost:11434
#   - PyInstaller packaging tip: Use PyInstaller to package the application into a standalone executable
#   - First-run checklist: Ensure Ollama endpoint is running, configure application settings, and load files for analysis
#   - Tkinter version gotchas: No known issues with Tkinter version