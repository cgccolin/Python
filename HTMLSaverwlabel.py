import tkinter as tk
from tkinter import filedialog
import re
import os
from datetime import datetime
import requests
from io import BytesIO
from PIL import Image, ImageTk

# Define MCC brand colors for consistent UI styling
GOLD = '#C99700'
GRAY = '#888B8D'
BLACK = '#000000'
WHITE = '#FFFFFF'


def get_logical_name(html_content: str) -> str:
    """
    Extract a logical name from the HTML content based on priority patterns.
    
    This function searches for specific HTML elements in order of priority to derive
    a meaningful filename. If no patterns match, it falls back to a timestamp-based name.
    
    Args:
        html_content (str): The HTML string to analyze.
    
    Returns:
        str: A cleaned, valid filename string.
    """
    patterns = [
        r'<div class="exlheader"><b[^>]*>(.+?)</b></div>',
        r'<div class="sectiontext">(.+?)</div>',
        r'<title>(.+?)</title>',
        r'<h1>(.+?)</h1>',
        r'<b[^>]*>([^<]+)</b>'
    ]
    
    for pattern in patterns:
        if match := re.search(pattern, html_content, re.DOTALL):
            name = match.group(1).strip()
            break
    else:
        # Fallback: Use current timestamp for uniqueness
        name = f"HTML_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Clean the name for filesystem compatibility
    name = re.sub(r'[<>:"/\\|?*]', '', name)  # Remove invalid filename characters
    name = re.sub(r'\s+', '_', name)          # Replace whitespace with underscores
    name = name[:50]                          # Truncate to reasonable length

    return name


def detect_page_type(html_content: str) -> str:
    """
    Determine the page type based on HTML structure patterns.
    
    Identifies if the page is a 'tile' page (with card tiles), 'list' page (with tables),
    or 'text' page (neither).
    
    Args:
        html_content (str): The HTML string to analyze.
    
    Returns:
        str: The detected page type ('tile', 'list', or 'text').
    """
    # Pre-compile regex patterns for efficiency
    tile_pattern = re.compile(r'class="child w3-card tile"', re.DOTALL)
    list_pattern = re.compile(r'<table.*class="w3-table w3-striped w3-bordered w3-border"', re.DOTALL)

    if tile_pattern.search(html_content):
        return "tile"
    elif list_pattern.search(html_content):
        return "list"
    else:
        return "text"


def save_html(content: str, folder: str) -> str:
    """
    Save the HTML content to a file in the specified folder with a logical name and type suffix.
    
    Generates a unique filename by appending a counter if conflicts occur.
    
    Args:
        content (str): The HTML content to save.
        folder (str): The directory path to save the file.
    
    Returns:
        str: A message indicating success or error.
    """
    if not content:
        return "No content to save."

    base_name = get_logical_name(content)
    page_type = detect_page_type(content)
    base_name_with_type = f"{base_name}_{page_type}"
    
    counter = 0
    file_path = os.path.join(folder, f"{base_name_with_type}.html")
    
    # Ensure filename uniqueness by incrementing counter
    while os.path.exists(file_path):
        counter += 1
        file_path = os.path.join(folder, f"{base_name_with_type}_{counter}.html")
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Saved as: {file_path}"
    except Exception as e:
        return f"Error saving file: {str(e)}"


# Initialize the main GUI window
root = tk.Tk()
root.title("HTML Input Collector")
root.configure(bg=WHITE)

# Load and display MCC logo with fallback to text label
logo_url = "https://www.monroecc.edu/fileadmin/SiteFiles/GeneralContent/depts/brand-toolkit/images/2015_logos/horizontal_logos/MCC_logo_horiz_color_rgb.png"
try:
    response = requests.get(logo_url, timeout=5)  # Add timeout for better reliability
    response.raise_for_status()
    img_data = BytesIO(response.content)
    img = Image.open(img_data)
    img = img.resize((300, 75), Image.LANCZOS)
    photo = ImageTk.PhotoImage(img)
    logo_label = tk.Label(root, image=photo, bg=WHITE)
    logo_label.image = photo  # Retain reference to prevent garbage collection
    logo_label.pack(pady=10)
except Exception as e:
    print(f"Error loading logo: {e}")
    fallback_label = tk.Label(root, text="Monroe Community College", font=("Arial", 16, "bold"), bg=WHITE, fg=BLACK)
    fallback_label.pack(pady=10)

# Set up output folder selection with default path
output_folder = tk.StringVar(value=os.path.expanduser("~/Desktop/htmlscripts/scripts"))

def choose_folder():
    """Open a directory selection dialog and update the output folder."""
    folder = filedialog.askdirectory()
    if folder:
        output_folder.set(folder)
        folder_label.config(text=f"Output Folder: {folder}")

choose_button = tk.Button(root, text="Choose Folder", command=choose_folder, bg=GOLD, fg=BLACK, activebackground=GRAY, activeforeground=WHITE)
choose_button.pack(pady=10)

folder_label = tk.Label(root, text=f"Output Folder: {output_folder.get()}", bg=WHITE, fg=BLACK, wraplength=600)  # Add wraplength for long paths
folder_label.pack()

# Create text widget for HTML input
html_text = tk.Text(root, height=15, width=80, wrap='word', bg=WHITE, fg=BLACK)
html_text.pack(pady=10)

# Create console for logging messages
console = tk.Text(root, height=10, width=80, state='disabled', wrap='word', bg=GRAY, fg=BLACK)
console.pack(pady=10)

def log_message(message: str):
    """Log a message to the console widget."""
    console.config(state='normal')
    console.insert(tk.END, f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")  # Add timestamp for better logging
    console.see(tk.END)
    console.config(state='disabled')

# Bind paste event to process HTML after a short delay
def on_paste(event):
    root.after(100, process_html)

def process_html():
    """Process and save pasted HTML content, then clear the input."""
    content = html_text.get("1.0", tk.END).strip()
    if content:
        folder = output_folder.get()
        os.makedirs(folder, exist_ok=True)  # Ensure folder exists
        message = save_html(content, folder)
        log_message(message)
        html_text.delete("1.0", tk.END)

html_text.bind("<<Paste>>", on_paste)
html_text.bind("<Control-v>", on_paste)  # Explicitly bind Ctrl+V for cross-platform reliability

# Display initial instructions in console
log_message("Paste your HTML content into the text box above (e.g., via Ctrl+V). It will be processed and saved automatically.")

# Dynamically resize window to fit content
root.update_idletasks()
root.geometry(f"{root.winfo_reqwidth() + 20}x{root.winfo_reqheight() + 20}")  # Add padding for aesthetics

root.mainloop()