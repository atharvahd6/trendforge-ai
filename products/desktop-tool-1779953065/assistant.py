Here is a comprehensive Python Tkinter desktop application that includes a calendar assistant with functionality to create and view events, as well as ask LLaMA for the best time for an event.


import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import subprocess
import threading

class CalendarAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title('Calendar Assistant')
        self.root.geometry('800x600')
        self.db = sqlite3.connect('calendar.db')
        self.cursor = self.db.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS events
            (id INTEGER PRIMARY KEY, title TEXT, description TEXT, date TEXT, time TEXT)
        ''')
        self.db.commit()
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, expand=True)
        self.frame1 = tk.Frame(self.notebook)
        self.frame2 = tk.Frame(self.notebook)
        self.notebook.add(self.frame1, text='New Event')
        self.notebook.add(self.frame2, text='View Events')
        self.create_new_event_frame()
        self.create_view_events_frame()

    def create_new_event_frame(self):
        tk.Label(self.frame1, text='Title').grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self.frame1, text='Description').grid(row=1, column=0, padx=5, pady=5)
        tk.Label(self.frame1, text='Date').grid(row=2, column=0, padx=5, pady=5)
        tk.Label(self.frame1, text='Time').grid(row=3, column=0, padx=5, pady=5)
        self.title = tk.StringVar()
        self.description = tk.StringVar()
        self.date = tk.StringVar()
        self.time = tk.StringVar()
        tk.Entry(self.frame1, textvariable=self.title).grid(row=0, column=1, padx=5, pady=5)
        tk.Entry(self.frame1, textvariable=self.description).grid(row=1, column=1, padx=5, pady=5)
        tk.Entry(self.frame1, textvariable=self.date).grid(row=2, column=1, padx=5, pady=5)
        tk.Entry(self.frame1, textvariable=self.time).grid(row=3, column=1, padx=5, pady=5)
        tk.Button(self.frame1, text='Create Event', command=self.create_event).grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        tk.Button(self.frame1, text='Ask LLaMA', command=self.ask_llama_threaded).grid(row=5, column=0, columnspan=2, padx=5, pady=5)

    def create_view_events_frame(self):
        self.events_frame = tk.Frame(self.frame2)
        self.events_frame.pack(fill='both', expand=True)
        self.view_events()

    def create_event(self):
        self.cursor.execute('INSERT INTO events (title, description, date, time) VALUES (?, ?, ?, ?)',
                            (self.title.get(), self.description.get(), self.date.get(), self.time.get()))
        self.db.commit()
        self.view_events()

    def view_events(self):
        for widget in self.events_frame.winfo_children():
            widget.destroy()
        self.cursor.execute('SELECT * FROM events')
        events = self.cursor.fetchall()
        for i, event in enumerate(events):
            tk.Label(self.events_frame, text=f'Title: {event[1]}').grid(row=i, column=0, padx=5, pady=5)
            tk.Label(self.events_frame, text=f'Description: {event[2]}').grid(row=i, column=1, padx=5, pady=5)
            tk.Label(self.events_frame, text=f'Date: {event[3]}').grid(row=i, column=2, padx=5, pady=5)
            tk.Label(self.events_frame, text=f'Time: {event[4]}').grid(row=i, column=3, padx=5, pady=5)
            tk.Button(self.events_frame, text='Delete Event', command=lambda event_id=event[0]: self.delete_event(event_id)).grid(row=i, column=4, padx=5, pady=5)

    def ask_llama(self):
        prompt = f'What is the best time for {self.title.get()} on {self.date.get()}?'
        try:
            process = subprocess.Popen(['llama3', '--prompt', prompt], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            if process.returncode == 0:
                return output.decode('utf-8')
            else:
                return f"An error occurred: {error.decode('utf-8')}"
        except Exception as e:
            return f"An error occurred: {str(e)}"

    def ask_llama_threaded(self):
        thread = threading.Thread(target=self.display_llama_response)
        thread.start()

    def display_llama_response(self):
        response = self.ask_llama()
        if response:
            messagebox.showinfo('LLaMA Response', response)

    def delete_event(self, event_id):
        self.cursor.execute('DELETE FROM events WHERE id=?', (event_id,))
        self.db.commit()
        self.view_events()

root = tk.Tk()
app = CalendarAssistant(root)
root.mainloop()


In the provided code:

- I've moved the `ask_llama` function call to a separate thread to prevent blocking the GUI when asking LLaMA for a response.
- Added a new `display_llama_response` function that gets called in the separate thread, which displays the LLaMA response in a message box.
- Added a `delete_event` method to handle deleting events and updated the `view_events` method to include a delete button for each event.
- Moved the creation of the delete button for each event to the `view_events` method, so it re-appears when events are re-loaded.
- Improved the error handling in the `ask_llama` function to provide more informative error messages.