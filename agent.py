import os
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import subprocess
from datetime import datetime

# ==========================================
# 1. DATABASE & ENTERPRISE STORAGE SETUP
# ==========================================
DB_PATH = "enterprise_calendar.db"

def init_db():
    """Initializes the secure local database for storing meeting metadata."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            attendees TEXT,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

# ==========================================
# 2. OLLAMA OFFLINE INTELLIGENCE PIPELINE
# ==========================================
def query_local_ai(prompt):
    """Passes scheduling data securely to Ollama without cloud leakage."""
    try:
        # Calls Ollama via native system subprocess
        result = subprocess.run(
            ["ollama", "run", "llama3", prompt],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8"
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Local AI Assistant offline. Ensure Ollama is running 'llama3'. (Error: {e})"

# ==========================================
# 3. ENTERPRISE GUI ARCHITECTURE
# ==========================================
class EnterpriseCalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Intel-Calendar (Air-Gapped)")
        self.root.geometry("900x600")
        self.root.configure(bg="#2c3e50")
        
        # Style Configuration
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.create_widgets()
        self.load_events()

    def create_widgets(self):
        # Left Panel: Event Creation & AI Tools
        left_panel = tk.Frame(self.root, bg="#34495e", width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        tk.Label(left_panel, text="Schedule Management", fg="white", bg="#34495e", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Input Form Fields
        tk.Label(left_panel, text="Meeting Title:", fg="lightgray", bg="#34495e").pack(anchor="w", padx=10)
        self.ent_title = ttk.Entry(left_panel, width=35)
        self.ent_title.pack(padx=10, pady=2)
        
        tk.Label(left_panel, text="Date (YYYY-MM-DD):", fg="lightgray", bg="#34495e").pack(anchor="w", padx=10)
        self.ent_date = ttk.Entry(left_panel, width=35)
        self.ent_date.insert(0, datetime.today().strftime('%Y-%m-%d'))
        self.ent_date.pack(padx=10, pady=2)
        
        tk.Label(left_panel, text="Time (HH:MM):", fg="lightgray", bg="#34495e").pack(anchor="w", padx=10)
        self.ent_time = ttk.Entry(left_panel, width=35)
        self.ent_time.pack(padx=10, pady=2)

        tk.Label(left_panel, text="Attendees (Separated by commas):", fg="lightgray", bg="#34495e").pack(anchor="w", padx=10)
        self.ent_attendees = ttk.Entry(left_panel, width=35)
        self.ent_attendees.pack(padx=10, pady=2)
        
        tk.Label(left_panel, text="Agenda / Context:", fg="lightgray", bg="#34495e").pack(anchor="w", padx=10)
        self.txt_desc = tk.Text(left_panel, width=30, height=4, font=("Arial", 10))
        self.txt_desc.pack(padx=10, pady=5)
        
        # Operation Buttons
        btn_save = tk.Button(left_panel, text="🔒 Save Secure Event", bg="#27ae60", fg="white", font=("Arial", 10, "bold"), command=self.save_event)
        btn_save.pack(fill=tk.X, padx=10, pady=5)
        
        # AI Smart Operations Pane
        tk.Label(left_panel, text="AI Executive Assistant", fg="white", bg="#34495e", font=("Arial", 12, "bold")).pack(pady=15)
        
        btn_brief = tk.Button(left_panel, text="🧠 Generate Daily Executive Brief", bg="#2980b9", fg="white", command=self.generate_daily_brief)
        btn_brief.pack(fill=tk.X, padx=10, pady=5)

        # Right Panel: Outlook-Style Agenda List Viewer
        right_panel = tk.Frame(self.root, bg="#2c3e50")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(right_panel, text="Corporate Agenda Timeline", fg="white", bg="#2c3e50", font=("Arial", 14, "bold")).pack(pady=5)
        
        # Columns for Calendar Data List View
        columns = ("id", "title", "date", "time", "attendees")
        self.tree = ttk.Treeview(right_panel, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Meeting Topic")
        self.tree.heading("date", text="Scheduled Date")
        self.tree.heading("time", text="Time")
        self.tree.heading("attendees", text="Internal Personnel")
        
        self.tree.column("id", width=30, anchor="center")
        self.tree.column("title", width=180)
        self.tree.column("date", width=100, anchor="center")
        self.tree.column("time", width=70, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)

    # ==========================================
# 4. BACKEND LOGIC & DATA OPERATIONS
# ==========================================
    def save_event(self):
        title = self.ent_title.get().strip()
        date = self.ent_date.get().strip()
        time = self.ent_time.get().strip()
        attendees = self.ent_attendees.get().strip()
        desc = self.txt_desc.get("1.0", tk.END).strip()
        
        if not title or not date or not time:
            messagebox.showerror("Validation Error", "Topic, Date, and Time are mandatory parameters.")
            return
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO events (title, date, time, attendees, description) VALUES (?, ?, ?, ?, ?)",
                       (title, date, time, attendees, desc))
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Success", "Event locked into local hardware ledger.")
        self.clear_form()
        self.load_events()

    def load_events(self):
        # Clear existing items in Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, date, time, attendees FROM events ORDER BY date ASC, time ASC")
        rows = cursor.fetchall()
        for row in rows:
            self.tree.insert("", tk.END, values=row)
        conn.close()

    def clear_form(self):
        self.ent_title.delete(0, tk.END)
        self.ent_time.delete(0, tk.END)
        self.ent_attendees.delete(0, tk.END)
        self.txt_desc.delete("1.0", tk.END)

    def generate_daily_brief(self):
        """Compiles calendar data locally and requests an analytical brief from Ollama."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT title, time, attendees, description FROM events WHERE date = ?", (self.ent_date.get().strip(),))
        meetings = cursor.fetchall()
        conn.close()
        
        if not meetings:
            messagebox.showinfo("AI Executive Brief", "No corporate items scheduled for this date sequence.")
            return
            
        # Format calendar rows into an analytical text block for Ollama
        agenda_context = f"Date: {self.ent_date.get().strip()}\n"
        for i, m in enumerate(meetings, 1):
            agenda_context += f"- Meeting {i}: Title: {m[0]} at {m[1]} | Internal Staff: {m[2]} | Details: {m[3]}\n"
            
        ai_prompt = f"""
        You are a highly efficient corporate executive chief of staff. 
        Review the following corporate calendar entries and provide an intense, bulleted executive briefing summary.
        Identify potential workflow preparation items, emphasize high-priority meetings, and recommend specific strategies to tackle the day efficiently.

        DATA LEDGER:
        {agenda_context}
        """
        
        # Display loading notification, then run the subprocess
        messagebox.showinfo("Processing", "Local AI analyzing internal ledger context... Please click OK to finalize calculations.")
        brief_result = query_local_ai(ai_prompt)
        
        # Show output window
        brief_window = tk.Toplevel(self.root)
        brief_window.title("AI Intelligence Daily Briefing")
        brief_window.geometry("500x400")
        
        txt_output = tk.Text(brief_window, wrap=tk.WORD, font=("Arial", 10))
        txt_output.insert(tk.END, brief_result)
        txt_output.config(state=tk.DISABLED)
        txt_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# ==========================================
# 5. EXECUTION LAYER
# ==========================================
if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = EnterpriseCalendarApp(root)
    root.mainloop()
