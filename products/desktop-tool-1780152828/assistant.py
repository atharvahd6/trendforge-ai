import os
import re
import json
from subprocess import Popen, PIPE
from PyPDF2 import PdfReader
import markdown

# Define the constants
POLICY_RULEBOOK = 'path_to_policy_rulebook.pdf'
USER_HISTORY_LOG = 'path_to_user_history_log'
THE_DENIAL_TEXT = 'path_to_denial_text.txt'

def read_policy_rulebook(file_path):
    """Reads the policy rulebook from a PDF file."""
    reader = PdfReader(file_path)
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text

def read_user_history_log(directory_path):
    """Reads the user history log from a directory."""
    text = ''
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as file:
                    text += file.read() + '\n'
            except Exception as e:
                print(f"Error reading file {filename}: {e}")
    return text

def read_denial_text(file_path):
    """Reads the denial text from a text file."""
    with open(file_path, 'r') as file:
        return file.read()

def extract_rejection_clause(text):
    """Extracts the rejection clause from the denial text."""
    # This is a simple example and may need to be adjusted based on the format of the denial text
    return re.search(r'Reason Code: (.*?)\.', text).group(1)

def query_policy_rulebook(policy_rulebook, rejection_clause):
    """Queries the policy rulebook to find the exact page, section, and line conditions required to satisfy or bypass the rejection clause."""
    # This is a simple example and may need to be adjusted based on the format of the policy rulebook
    pages = policy_rulebook.split('\n\n')
    for page in pages:
        sections = page.split('\n')
        for section in sections:
            lines = section.split('\n')
            for line in lines:
                if re.search(rejection_clause, line):
                    return page, section, line

def perform_evidentiary_audit(policy_rulebook, user_history_log, rejection_clause):
    """Performs an evidentiary audit to extract proof that the user actually met the criteria."""
    # This is a simple example and may need to be adjusted based on the format of the policy rulebook and user history log
    evidence_grid = []
    pages = policy_rulebook.split('\n\n')
    for page in pages:
        sections = page.split('\n')
        for section in sections:
            lines = section.split('\n')
            for line in lines:
                if re.search(rejection_clause, line):
                    user_history_log_lines = user_history_log.split('\n')
                    for user_history_log_line in user_history_log_lines:
                        if re.search(line, user_history_log_line):
                            evidence_grid.append((rejection_clause, page, section, user_history_log_line))
    return evidence_grid

def generate_appeals_brief(evidence_grid, rejection_clause):
    """Generates an appeals brief based on the evidence grid and rejection clause."""
    executive_summary = f"The denial of {rejection_clause} is incorrect because the user's data satisfies the rulebook."
    evidence_grid_table = "| Rejection Claim | Exact Rulebook Page/Clause | User Document Proof & Timestamp |\n| --- | --- | --- |\n"
    for row in evidence_grid:
        evidence_grid_table += f"| {row[0]} | {row[1]} | {row[3]} |\n"
    response_template = f"Dear [Institution],\n\nPlease review the attached evidence grid and reconsider the denial of {rejection_clause}.\n\nSincerely,\n[User]"
    return executive_summary, evidence_grid_table, response_template

def main():
    policy_rulebook = read_policy_rulebook(POLICY_RULEBOOK)
    user_history_log = read_user_history_log(USER_HISTORY_LOG)
    denial_text = read_denial_text(THE_DENIAL_TEXT)
    rejection_clause = extract_rejection_clause(denial_text)
    page, section, line = query_policy_rulebook(policy_rulebook, rejection_clause)
    evidence_grid = perform_evidentiary_audit(policy_rulebook, user_history_log, rejection_clause)
    executive_summary, evidence_grid_table, response_template = generate_appeals_brief(evidence_grid, rejection_clause)
    
    # Generate the markdown file
    markdown_text = f"# Appeals Brief\n\n## Executive Summary\n{executive_summary}\n\n## The Evidence Grid\n{evidence_grid_table}\n\n## The Response Template\n{response_template}"
    with open('appeals_brief.md', 'w') as file:
        file.write(markdown_text)

if __name__ == "__main__":
    main()

Note that this is a basic example and may need to be adjusted based on the format of the policy rulebook, user history log, and denial text. Additionally, this script assumes that the policy rulebook is a PDF file and the user history log is a directory containing text files. The `perform_evidentiary_audit` function uses a simple string matching approach to extract proof from the user history log, which may not be sufficient for more complex cases. 

Please ensure to replace the 'path_to_policy_rulebook.pdf', 'path_to_user_history_log', and 'path_to_denial_text.txt' placeholders with the actual paths to your files and directories. 

Finally, this script generates a markdown file named `appeals_brief.md` in the current working directory, which contains the executive summary, evidence grid table, and response template.