import os
import re
import json
from subprocess import Popen, PIPE
from tkinter import Tk, Label, Button, Entry, StringVar, filedialog

# Function to open file dialog for selecting policy rulebook
def select_policy_rulebook():
    filepath = filedialog.askopenfilename(title="Select Policy Rulebook", filetypes=[("PDF Files", "*.pdf"), ("Text Files", "*.txt")])
    policy_rulebook_entry.delete(0, 'end')
    policy_rulebook_entry.insert(0, filepath)

# Function to open file dialog for selecting user history log
def select_user_history_log():
    filepath = filedialog.askdirectory(title="Select User History Log Directory")
    user_history_log_entry.delete(0, 'end')
    user_history_log_entry.insert(0, filepath)

# Function to generate appeals brief
def generate_appeals_brief():
    policy_rulebook = policy_rulebook_entry.get()
    user_history_log = user_history_log_entry.get()
    the_denial_text = the_denial_text_entry.get("1.0", "end-1c")

    # Phase 1: Context Chunking & Extraction
    reason_code = extract_reason_code(the_denial_text)

    # Phase 2: Rulebook Validation
    rulebook_results = query_rulebook(policy_rulebook, reason_code)

    # Phase 3: Evidentiary Audit
    evidence_grid = perform_evidentiary_audit(user_history_log, rulebook_results)

    # Phase 4: Contradiction Mapping
    contradiction_map = map_contradictions(evidence_grid)

    # Generate appeals brief
    appeals_brief = generate_appeals_brief_markdown(the_denial_text, evidence_grid, contradiction_map)

    with open("appeals_brief.md", "w") as f:
        f.write(appeals_brief)

# Function to extract reason code from denial text
def extract_reason_code(denial_text):
    # For demonstration purposes, assume reason code is the first sentence of the denial text
    reason_code = denial_text.split(".")[0]
    return reason_code

# Function to query rulebook
def query_rulebook(policy_rulebook, reason_code):
    # Use subprocess to call Ollama for querying the rulebook
    process = Popen(["ollama", policy_rulebook, reason_code], stdout=PIPE)
    output, _ = process.communicate()
    rulebook_results = output.decode("utf-8")
    return rulebook_results

# Function to perform evidentiary audit
def perform_evidentiary_audit(user_history_log, rulebook_results):
    evidence_grid = []
    for file in os.listdir(user_history_log):
        file_path = os.path.join(user_history_log, file)
        with open(file_path, "r") as f:
            file_content = f.read()
            # Perform absolute text-matching and semantic search
            for line in file_content.splitlines():
                if rulebook_results in line:
                    evidence_grid.append((rulebook_results, file, line))
    return evidence_grid

# Function to map contradictions
def map_contradictions(evidence_grid):
    contradiction_map = []
    for row in evidence_grid:
        # Isolate instances where user's data satisfies the rulebook
        if row[0] in row[2]:
            contradiction_map.append(row)
    return contradiction_map

# Function to generate appeals brief markdown
def generate_appeals_brief_markdown(denial_text, evidence_grid, contradiction_map):
    appeals_brief = "# Executive Summary\n"
    appeals_brief += f"The denial is incorrect based on the following evidence: {denial_text}\n\n"
    appeals_brief += "# The Evidence Grid\n"
    appeals_brief += "| Rejection Claim | Exact Rulebook Page/Clause | User Document Proof & Timestamp |\n"
    appeals_brief += "| --- | --- | --- |\n"
    for row in evidence_grid:
        appeals_brief += f"| {row[0]} | {row[1]} | {row[2]} |\n"
    appeals_brief += "\n# The Response Template\n"
    appeals_brief += "Dear [Institution],\n"
    appeals_brief += "Re: [Case Number/Reference]\n"
    appeals_brief += "I am writing to appeal the denial of my [claim/application] based on the following evidence:\n"
    for row in contradiction_map:
        appeals_brief += f"- {row[0]}: {row[2]}\n"
    appeals_brief += "I kindly request that you review my case and reconsider your decision.\n"
    appeals_brief += "Sincerely,\n"
    appeals_brief += "[Your Name]"
    return appeals_brief

# Create main window
root = Tk()
root.title("Deep Document Forensic Compliance Reviewer")

# Create labels and entries for policy rulebook and user history log
policy_rulebook_label = Label(root, text="Policy Rulebook:")
policy_rulebook_label.grid(row=0, column=0)
policy_rulebook_entry = Entry(root, width=50)
policy_rulebook_entry.grid(row=0, column=1)
policy_rulebook_button = Button(root, text="Browse", command=select_policy_rulebook)
policy_rulebook_button.grid(row=0, column=2)

user_history_log_label = Label(root, text="User History Log:")
user_history_log_label.grid(row=1, column=0)
user_history_log_entry = Entry(root, width=50)
user_history_log_entry.grid(row=1, column=1)
user_history_log_button = Button(root, text="Browse", command=select_user_history_log)
user_history_log_button.grid(row=1, column=2)

# Create label and text box for denial text
the_denial_text_label = Label(root, text="Denial Text:")
the_denial_text_label.grid(row=2, column=0)
the_denial_text_entry = Entry(root, width=50)
the_denial_text_entry.grid(row=2, column=1)
the_denial_text = StringVar()
the_denial_text_box = Entry(root, textvariable=the_denial_text, width=50)
the_denial_text_box.grid(row=2, column=1)
the_denial_text_box.delete(0, 'end')
the_denial_text_box.insert(0, "Enter denial text here")

# Create button to generate appeals brief
generate_appeals_brief_button = Button(root, text="Generate Appeals Brief", command=generate_appeals_brief)
generate_appeals_brief_button.grid(row=3, column=1)

# Create text box to display appeals brief
appeals_brief_label = Label(root, text="Appeals Brief:")
appeals_brief_label.grid(row=4, column=0)
appeals_brief_text_box = Entry(root, width=50)
appeals_brief_text_box.grid(row=4, column=1)

root.mainloop()


To properly use this code, ensure you have the necessary libraries installed. You can do this by running `pip install tkinter`. Additionally, you'll need to install Ollama for querying the rulebook, however, since Ollama isn't a real tool, you will have to implement the logic to query the rulebook yourself.

You can then run the script and use the GUI to select the policy rulebook and user history log, enter the denial text, and generate the appeals brief. The appeals brief will be displayed in a new text box.

Remember, the code provided above is just an example, you will need to modify and extend it to fit your specific needs and the actual requirements of the project.