import os
import re
import json
import subprocess
from PIL import Image
from pdf2image import convert_from_path
from datetime import datetime

# Define the paths and variables
POLICY_RULEBOOK = "path_to_policy_rulebook.pdf"
USER_HISTORY_LOG = "path_to_user_history_log"
THE_DENIAL_TEXT = "path_to_denial_text.txt"

def context_chunking_extraction(the_denial_text):
    """
    Phase 1: Context Chunking & Extraction.
    Parse THE_DENIAL_TEXT to identify the exact "Reason Code" or specific clause the institution is using to reject the user.
    """
    with open(the_denial_text, 'r') as f:
        text = f.read()
    
    # Use regular expression to extract the reason code or clause
    reason_code = re.search(r'Reason Code: (.+)', text)
    if reason_code:
        return reason_code.group(1)
    else:
        # If reason code is not found, try to extract the specific clause
        clause = re.search(r'Clause (.+)', text)
        if clause:
            return clause.group(1)
        else:
            return None

def rulebook_validation(policy_rulebook, reason_code):
    """
    Phase 2: Rulebook Validation.
    Query POLICY_RULEBOOK using the identified rejection clause.
    The agent must locate the exact page, section, and line conditions required to satisfy or bypass that clause.
    """
    # Convert the pdf to images
    images = convert_from_path(policy_rulebook)
    
    # Initialize variables to store the page, section, and line conditions
    page = None
    section = None
    line_conditions = []
    
    # Iterate over the images
    for i, image in enumerate(images):
        # Save the image to a temporary file
        image.save(f'temp_image_{i}.jpg')
        
        # Use tesseract to extract the text from the image
        text = subprocess.check_output(['tesseract', f'temp_image_{i}.jpg', 'stdout']).decode('utf-8')
        
        # Check if the reason code is in the text
        if reason_code in text:
            # If the reason code is found, extract the page, section, and line conditions
            page = i + 1
            section = re.search(r'Section (.+)', text)
            if section:
                section = section.group(1)
            line_conditions = re.findall(r'Line (\d+): (.+)', text)
            
            # Remove the temporary image file
            os.remove(f'temp_image_{i}.jpg')
            break
    
    return page, section, line_conditions

def evidentiary_audit(user_history_log, reason_code, page, section, line_conditions):
    """
    Phase 3: Evidentiary Audit.
    Cross-reference those specific rules against the USER_HISTORY_LOG.
    The agent must perform an absolute text-matching and semantic search to extract proof that the user actually met the criteria.
    """
    # Initialize a list to store the evidence
    evidence = []
    
    # Iterate over the files in the user history log
    for file in os.listdir(user_history_log):
        # Check if the file is a text file
        if file.endswith('.txt'):
            # Open the file and read the text
            with open(os.path.join(user_history_log, file), 'r') as f:
                text = f.read()
            
            # Check if the reason code is in the text
            if reason_code in text:
                # If the reason code is found, extract the evidence
                evidence.append((file, text))
    
    return evidence

def contradiction_mapping(evidence, page, section, line_conditions):
    """
    Phase 4: Contradiction Mapping.
    Isolate any instances where the user's data satisfies the rulebook, proving the institution's denial is factually incorrect or legally inconsistent.
    """
    # Initialize a dictionary to store the contradiction mapping
    contradiction_mapping = {}
    
    # Iterate over the evidence
    for file, text in evidence:
        # Iterate over the line conditions
        for line_condition in line_conditions:
            # Check if the line condition is in the text
            if line_condition[1] in text:
                # If the line condition is found, add it to the contradiction mapping
                if line_condition[0] not in contradiction_mapping:
                    contradiction_mapping[line_condition[0]] = []
                contradiction_mapping[line_condition[0]].append((file, text))
    
    return contradiction_mapping

def generate_appeals_brief(contradiction_mapping, reason_code, page, section, line_conditions):
    """
    Generate the appeals brief.
    """
    # Initialize the appeals brief
    appeals_brief = '# Executive Summary\n'
    appeals_brief += f'The denial of {reason_code} is incorrect because the user\'s data satisfies the rulebook.\n\n'
    
    # Add the evidence grid
    appeals_brief += '# The Evidence Grid\n'
    appeals_brief += '| Rejection Claim | Exact Rulebook Page/Clause | User Document Proof & Timestamp |\n'
    appeals_brief += '| --- | --- | --- |\n'
    for line_condition, evidence in contradiction_mapping.items():
        appeals_brief += f'| {reason_code} | {page}, {section}, {line_condition} | {evidence[0][0]} |\n'
    
    # Add the response template
    appeals_brief += '\n# The Response Template\n'
    appeals_brief += 'Dear [Institution],\n'
    appeals_brief += f'I am writing to appeal the denial of {reason_code}.\n'
    appeals_brief += 'As shown in the evidence grid above, the user\'s data satisfies the rulebook.\n'
    appeals_brief += 'Therefore, I request that you immediately review and reconsider your decision.\n'
    appeals_brief += 'Sincerely,\n'
    appeals_brief += '[Your Name]\n'
    
    return appeals_brief

def main():
    # Phase 1: Context Chunking & Extraction
    reason_code = context_chunking_extraction(THE_DENIAL_TEXT)
    
    # Phase 2: Rulebook Validation
    page, section, line_conditions = rulebook_validation(POLICY_RULEBOOK, reason_code)
    
    # Phase 3: Evidentiary Audit
    evidence = evidentiary_audit(USER_HISTORY_LOG, reason_code, page, section, line_conditions)
    
    # Phase 4: Contradiction Mapping
    contradiction_mapping = contradiction_mapping(evidence, page, section, line_conditions)
    
    # Generate the appeals brief
    appeals_brief = generate_appeals_brief(contradiction_mapping, reason_code, page, section, line_conditions)
    
    # Save the appeals brief to a file
    with open('appeals_brief.md', 'w') as f:
        f.write(appeals_brief)

if __name__ == '__main__':
    main()