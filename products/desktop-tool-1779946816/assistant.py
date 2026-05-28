import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import pickle
import hashlib
from PIL import Image, ImageTk
import pytesseract
from pytesseract import Output
import csv
import datetime

class EasyExpense:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("EasyExpense")
        self.password = ""
        self.expenses = []
        self.load_expenses()

        # Create tabs
        self.tab_control = tk.Notebook(self.window)
        self.tab_control.pack(expand=1, fill="both")

        self.log_tab = tk.Frame(self.tab_control)
        self.receipt_tab = tk.Frame(self.tab_control)
        self.report_tab = tk.Frame(self.tab_control)
        self.budget_tab = tk.Frame(self.tab_control)
        self.export_tab = tk.Frame(self.tab_control)

        self.tab_control.add(self.log_tab, text="Log Expense")
        self.tab_control.add(self.receipt_tab, text="Receipt Scanner")
        self.tab_control.add(self.report_tab, text="Report")
        self.tab_control.add(self.budget_tab, text="Budget")
        self.tab_control.add(self.export_tab, text="Export")

        # Log Expense tab
        self.log_frame = tk.Frame(self.log_tab)
        self.log_frame.pack()

        tk.Label(self.log_frame, text="Category:").pack()
        self.category = tk.StringVar()
        tk.OptionMenu(self.log_frame, self.category, "Food", "Transport", "Entertainment").pack()

        tk.Label(self.log_frame, text="Date:").pack()
        self.date = tk.StringVar()
        tk.Entry(self.log_frame, textvariable=self.date).pack()

        tk.Label(self.log_frame, text="Amount:").pack()
        self.amount = tk.StringVar()
        tk.Entry(self.log_frame, textvariable=self.amount).pack()

        tk.Label(self.log_frame, text="Note:").pack()
        self.note = tk.StringVar()
        tk.Entry(self.log_frame, textvariable=self.note).pack()

        tk.Button(self.log_frame, text="Log Expense", command=self.log_expense).pack()

        # Receipt Scanner tab
        self.receipt_frame = tk.Frame(self.receipt_tab)
        self.receipt_frame.pack()

        tk.Button(self.receipt_frame, text="Select Receipt Image", command=self.select_receipt_image).pack()

        # Report tab
        self.report_frame = tk.Frame(self.report_tab)
        self.report_frame.pack()

        tk.Button(self.report_frame, text="Generate Report", command=self.generate_report).pack()

        # Budget tab
        self.budget_frame = tk.Frame(self.budget_tab)
        self.budget_frame.pack()

        tk.Label(self.budget_frame, text="Category:").pack()
        self.budget_category = tk.StringVar()
        tk.OptionMenu(self.budget_frame, self.budget_category, "Food", "Transport", "Entertainment").pack()

        tk.Label(self.budget_frame, text="Amount:").pack()
        self.budget_amount = tk.StringVar()
        tk.Entry(self.budget_frame, textvariable=self.budget_amount).pack()

        tk.Button(self.budget_frame, text="Set Budget", command=self.set_budget).pack()

        # Export tab
        self.export_frame = tk.Frame(self.export_tab)
        self.export_frame.pack()

        tk.Button(self.export_frame, text="Export to CSV", command=self.export_to_csv).pack()

        # Password protection
        self.password_frame = tk.Frame(self.window)
        self.password_frame.pack()

        tk.Label(self.password_frame, text="Password:").pack()
        self.password_entry = tk.StringVar()
        tk.Entry(self.password_frame, textvariable=self.password_entry, show="*").pack()

        tk.Button(self.password_frame, text="Set Password", command=self.set_password).pack()

        self.window.mainloop()

    def load_expenses(self):
        if os.path.exists("expenses.dat"):
            with open("expenses.dat", "rb") as f:
                self.expenses = pickle.load(f)

    def save_expenses(self):
        with open("expenses.dat", "wb") as f:
            pickle.dump(self.expenses, f)

    def log_expense(self):
        if self.password:
            expense = {
                "category": self.category.get(),
                "date": self.date.get(),
                "amount": self.amount.get(),
                "note": self.note.get()
            }
            self.expenses.append(expense)
            self.save_expenses()
            messagebox.showinfo("Expense logged", "Expense has been logged successfully")
        else:
            messagebox.showerror("Error", "Please set a password first")

    def select_receipt_image(self):
        if self.password:
            filename = filedialog.askopenfilename()
            if filename:
                # Use OCR to extract text from image
                text = pytesseract.image_to_string(Image.open(filename), output_type=Output.STRING)
                messagebox.showinfo("Receipt scanned", text)
        else:
            messagebox.showerror("Error", "Please set a password first")

    def generate_report(self):
        if self.password:
            # Generate report based on logged expenses
            report = ""
            for expense in self.expenses:
                report += f"Category: {expense['category']}, Date: {expense['date']}, Amount: {expense['amount']}, Note: {expense['note']}\n"
            messagebox.showinfo("Report", report)
        else:
            messagebox.showerror("Error", "Please set a password first")

    def set_budget(self):
        if self.password:
            # Set budget for selected category
            budget = {
                "category": self.budget_category.get(),
                "amount": self.budget_amount.get()
            }
            # Save budget to file
            with open("budget.dat", "w") as f:
                f.write(f"{budget['category']},{budget['amount']}")
            messagebox.showinfo("Budget set", "Budget has been set successfully")
        else:
            messagebox.showerror("Error", "Please set a password first")

    def export_to_csv(self):
        if self.password:
            # Export expenses to CSV file
            with open("expenses.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Category", "Date", "Amount", "Note"])
                for expense in self.expenses:
                    writer.writerow([expense["category"], expense["date"], expense["amount"], expense["note"]])
            messagebox.showinfo("Exported", "Expenses have been exported to expenses.csv")
        else:
            messagebox.showerror("Error", "Please set a password first")

    def set_password(self):
        password = self.password_entry.get()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        with open("password.dat", "w") as f:
            f.write(hashed_password)
        self.password = password
        messagebox.showinfo("Password set", "Password has been set successfully")

    def check_password(self):
        if os.path.exists("password.dat"):
            with open("password.dat", "r") as f:
                hashed_password = f.read()
            password = self.password_entry.get()
            if hashlib.sha256(password.encode()).hexdigest() == hashed_password:
                self.password = password
                return True
        return False

if __name__ == "__main__":
    app = EasyExpense()