import tkinter as tk
from tkinter import filedialog, ttk
from tkinter import messagebox
import os
import tempfile
from urllib.request import urlretrieve
from bs4 import BeautifulSoup
import shutil
from PIL import Image, ImageTk
import datetime
import threading

# Global variable for output directory, defaulting to user's Downloads folder
output_dir = os.path.expanduser("~/Downloads")

# Template HTML and CSS as strings
template_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Title</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header role="banner" class="header">
        <div class="header-container">
            <a href="#" class="header-logo">
                <span class="header-title">Page Title</span>
            </a>
            <button id="nav-toggle" class="nav-toggle" aria-label="Toggle navigation menu" aria-expanded="false" aria-controls="nav-menu">☰</button>
            <nav class="header-nav" id="nav-menu">
                <ul>
                    <li><a href="#" aria-current="page">Home</a></li>
                    <li><a href="#">Student Resource Guide</a></li>
                    <li><a href="#">Student Services</a></li>
                </ul>
            </nav>
        </div>
    </header>
    <main class="main">
        <div aria-live="polite" id="status-message"></div>
        <section class="intro"></section>
        <section class="ada-info"></section>
        <section class="navigation-tiles"></section>
        <div role="presentation" class="quick-links">
            <div id="quick-links-status" class="sr-only">Quick Links list collapsed</div>
            <button role="button" aria-expanded="false" aria-label="Quick Links list collapsed" aria-describedby="quick-links-status" id="quick-links-toggle" class="quick-links-toggle">
            Quick Links ▼
            </button>
            <div id="quick-links-content" class="quick-links-content">
                <ul role="list">
                    <li><a href="#" tabindex="-1" aria-label="MCC Home">MCC Home</a></li>
                    <li><a href="#" tabindex="-1" aria-label="Financial Aid">Financial Aid</a></li>
                    <li><a href="#" tabindex="-1" aria-label="Housing & Residence Life">Housing & Residence Life</a></li>
                    <li><a href="#" tabindex="-1" aria-label="Counseling Center">Counseling Center</a></li>
                    <li><a href="#" tabindex="-1" aria-label="Public Safety">Public Safety</a></li>
                    <li><a href="#" tabindex="-1" aria-label="211/LIFE LINE">211/LIFE LINE</a></li>
                </ul>
            </div>
        </div>
    </main>
    <footer class="footer">
        <div class="footer-container">
            <p>© 2025 Monroe Community College. All rights reserved.</p>
            <a href="#" class="footer-link">Contact MCC</a>
        </div>
    </footer>
    <script>
        // Navigation toggle functionality
        const navToggle = document.querySelector('.nav-toggle');
        const headerNav = document.querySelector('.header-nav');
        const links = headerNav.querySelectorAll('a');
        const firstLink = links[0];
        const lastLink = links[links.length - 1];
        const statusMessage = document.querySelector('#status-message');
        const header = document.querySelector('.header');
        // Updates the visual state and ARIA attributes of the navigation toggle
        function updateToggleVisual(isExpanded) {
            navToggle.textContent = isExpanded ? '✕' : '☰';
            navToggle.setAttribute('aria-label', isExpanded ? 'Close navigation menu' : 'Open navigation menu');
        }
        // Traps focus within the navigation menu when open
        function trapFocus(e) {
            if (!headerNav.classList.contains('active')) return;
            const isTabPressed = e.key === 'Tab';
            if (!isTabPressed) return;
            if (e.shiftKey) {
                if (document.activeElement === navToggle) {
                    lastLink.focus();
                    e.preventDefault();
                }
            } else {
                if (document.activeElement === lastLink) {
                    navToggle.focus();
                    e.preventDefault();
                }
            }
        }
        // Handles navigation toggle action
        function handleToggleAction() {
            const isExpanded = headerNav.classList.toggle('active');
            navToggle.setAttribute('aria-expanded', isExpanded);
            updateToggleVisual(isExpanded);
            if (isExpanded) {
                firstLink.focus();
                document.addEventListener('keydown', trapFocus);
                statusMessage.textContent = 'Navigation menu expanded';
            } else {
                document.removeEventListener('keydown', trapFocus);
                const nextFocusable = document.querySelector('.tile-link');
                if (nextFocusable) nextFocusable.focus();
                statusMessage.textContent = 'Navigation menu collapsed';
            }
        }
        navToggle.addEventListener('click', handleToggleAction);
        navToggle.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleToggleAction();
            }
        });
        updateToggleVisual(false);
        // Header scroll behavior to hide/show header on scroll
        let lastScrollY = window.scrollY;
        window.addEventListener('scroll', () => {
            const currentScrollY = window.scrollY;
            if (currentScrollY > lastScrollY && currentScrollY > 50) {
                header.classList.add('hidden');
            } else {
                header.classList.remove('hidden');
            }
            lastScrollY = currentScrollY;
        });
        // Tile toggling functionality
        let currentExpandedTile = null;
        // Handles shift-tab on first link in expanded tile
        function handleFirstLinkShiftTab(event) {
            if (event.key === 'Tab' && event.shiftKey) {
                event.preventDefault();
                currentExpandedTile.focus();
            }
        }
        // Handles tab on last link in expanded tile
        function handleLastLinkTab(event) {
            if (event.key === 'Tab' && !event.shiftKey) {
                event.preventDefault();
                currentExpandedTile.focus();
            }
        }
        // Toggles visibility of a tile section
        function toggleSection(sectionId, tile) {
            const section = document.getElementById(sectionId);
            const tileElement = tile.querySelector('.tile');
            const tileText = tile.querySelector('.tile-text').textContent;
            const isActive = tileElement.classList.contains('active');
            document.querySelectorAll('.navigation-tile').forEach(t => {
                t.querySelector('.tile').classList.remove('active');
                t.setAttribute('aria-expanded', 'false');
            });
            document.querySelectorAll('.tile-group').forEach(group => {
                group.classList.remove('active');
                group.style.display = 'none';
                const links = group.querySelectorAll('.tile-link');
                if (links.length > 0) {
                    links[0].removeEventListener('keydown', handleFirstLinkShiftTab);
                    links[links.length - 1].removeEventListener('keydown', handleLastLinkTab);
                }
            });
            if (!isActive) {
                tileElement.classList.add('active');
                tile.setAttribute('aria-expanded', 'true');
                section.classList.add('active');
                section.style.display = 'block';
                statusMessage.textContent = `${tileText} has been expanded`;
                const links = section.querySelectorAll('.tile-link');
                if (links.length > 0) {
                    links[0].addEventListener('keydown', handleFirstLinkShiftTab);
                    links[links.length - 1].addEventListener('keydown', handleLastLinkTab);
                }
                currentExpandedTile = tile;
            } else {
                statusMessage.textContent = `${tileText} collapsed`;
                currentExpandedTile = null;
            }
        }
        // Handles keydown events for tile navigation
        function handleKeydown(event, sectionId, tile) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                toggleSection(sectionId, tile);
            } else if (event.key === 'Tab' && tile.getAttribute('aria-expanded') === 'true') {
                event.preventDefault();
                const section = document.getElementById(sectionId);
                const firstLink = section.querySelector('.tile-link');
                if (firstLink) {
                    firstLink.focus();
                }
            }
        }
        // Adds focus and hover event listeners to navigation tiles
        document.querySelectorAll('.navigation-tile').forEach(tile => {
            const tileText = tile.querySelector('.tile-text').textContent;
            tile.addEventListener('focus', () => {
                statusMessage.textContent = tileText;
            });
            tile.addEventListener('mouseenter', () => {
                statusMessage.textContent = tileText;
            });
        });
        // Quick links toggle functionality
        const quickLinksToggle = document.querySelector('.quick-links-toggle');
        const quickLinksContent = document.querySelector('.quick-links-content');
        const quickLinksStatus = document.querySelector('#quick-links-status');
        const quickLinks = quickLinksContent.querySelectorAll('a');
        const quickFirstLink = quickLinks[0];
        const quickLastLink = quickLinks[quickLinks.length - 1];
        // Updates the quick links toggle state
        function updateToggleState(isExpanded) {
            const stateText = `Quick Links list ${isExpanded ? 'expanded' : 'collapsed'}`;
            quickLinksToggle.setAttribute('aria-label', stateText);
            quickLinksStatus.textContent = stateText;
            quickLinksToggle.textContent = `Quick Links ${isExpanded ? '▲' : '▼'}`;
            quickLinks.forEach(link => {
                link.setAttribute('tabindex', isExpanded ? '0' : '-1');
            });
        }
        // Traps focus within quick links when expanded
        function trapQuickFocus(e) {
            if (!quickLinksContent.classList.contains('active')) return;
            const isTabPressed = e.key === 'Tab';
            if (!isTabPressed) return;
            if (e.shiftKey) {
                if (document.activeElement === quickLinksToggle) {
                    quickLastLink.focus();
                    e.preventDefault();
                }
            } else {
                if (document.activeElement === quickLastLink) {
                    quickLinksToggle.focus();
                    e.preventDefault();
                }
            }
        }
        // Handles quick links toggle action
        function handleQuickToggleAction() {
            const isExpanded = quickLinksContent.classList.toggle('active');
            quickLinksToggle.setAttribute('aria-expanded', isExpanded);
            updateToggleState(isExpanded);
            if (isExpanded) {
                quickFirstLink.focus();
                document.addEventListener('keydown', trapQuickFocus);
                statusMessage.textContent = 'Quick Links expanded';
            } else {
                document.removeEventListener('keydown', trapQuickFocus);
                const nextFocusable = document.querySelector('.footer-link');
                if (nextFocusable) nextFocusable.focus();
                statusMessage.textContent = 'Quick Links collapsed';
            }
        }
        quickLinksToggle.addEventListener('click', handleQuickToggleAction);
        quickLinksToggle.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleQuickToggleAction();
            }
        });
        updateToggleState(false);
    </script>
</body>
</html>
'''

css_string = '''
/* Reset default styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}
/* Body styles */
body {
    font-family: "Verdana", sans-serif;
    font-size: 16px;
    color: #000;
    background-color: #F9FAFB;
    line-height: 1.5;
}
/* Header styles */
.header {
    background-color: #c99700;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    position: sticky;
    top: 0;
    z-index: 1000;
    transition: transform 0.3s ease;
}
.header.hidden {
    transform: translateY(-100%);
}
.header-container {
    padding: 10px 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
}
.header-logo {
    display: flex;
    align-items: center;
    text-decoration: none;
}
.header-title {
    font-size: 24px;
    color: #000;
    font-weight: 700;
    font-family: Verdana, Geneva, sans-serif;
}
.nav-toggle {
    background: none;
    border: none;
    font-size: 24px;
    color: #000;
    cursor: pointer;
    display: block;
}
.header-nav {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background-color: #fff;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}
.header-nav.active {
    display: block;
}
.header-nav ul {
    list-style: none;
}
.header-nav li {
    padding: 10px 15px;
}
.header-nav a {
    color: #000;
    text-decoration: none;
    font-weight: 500;
    font-size: 16px;
    font-family: Verdana, Geneva, sans-serif;
    line-height: 1.6;
}
/* Screen reader only styles */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
}
/* Main content styles */
.main {
    padding: 15px;
    box-sizing: border-box;
}
.intro {
    margin-bottom: 20px;
}
.ada-info {
    margin-bottom: 20px;
}
.ada-info p {
    overflow-wrap: break-word;
    word-wrap: break-word;
    hyphens: auto;
    font-size: 14px;
    font-family: Verdana, Geneva, sans-serif;
}
.sub-add-text p {
    font-size: 14px;
    font-family: Verdana, Geneva, sans-serif;
}
.tile-group-container {
    margin-bottom: 20px;
}
.tile-group-container h3 {
    background-color: #C99700;
    color: #000;
    font-family: Verdana, Geneva, sans-serif;
    padding: 10px;
    padding-left: 25px;
    margin-bottom: 15px;
}
.tile-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-auto-rows: 110px;
    gap: 10px;
    padding: 10px;
    margin-bottom: 20px;
}
.tile-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-auto-rows: 110px;
    gap: 10px;
    padding: 5px;
    margin-bottom: 5px;
}
.tile-link {
    text-decoration: none;
    color: #000;
    display: block;
}
.navigation-tile {
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
}
.tile-link:hover .tile,
.tile-link:focus .tile {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.35);
}
.tile {
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    border-radius: 10px;
    box-shadow: 0 2px 3px 0;
    height: 110px;
    display: grid;
    grid-template-rows: 50px 60px;
    align-items: center;
    justify-items: center;
    text-align: center;
    overflow: hidden;
    transition: transform 0.3s ease, box-shadow 0.3s ease, background-color 0.3s ease;
    width: 100%;
}
.tile.active {
    background-color: #C99700;
    border: 2px solid #000;
}
.tile-icon {
    padding-top: 13px;
    transform: translateY(0);
    transition: transform 0.3s ease;
}
.tile-link:hover .tile-icon,
.tile-link:focus .tile-icon {
    transform: translateY(4px);
}
.tile-icon img {
    width: 45px;
    height: 45px;
}
.tile-text {
    font-size: 11px;
    padding: 0 5px;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.2;
    max-height: 43px;
    font-weight: 700;
    transform: translateY(0);
    transition: transform 0.3s ease;
    font-family: "Verdana";
}
.tile-link:hover .tile-text,
.tile-link:focus .tile-text {
    transform: translateY(4px);
}
.quick-links {
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    margin: 20px;
    max-width: 1200px;
}
.quick-links-toggle {
    width: 100%;
    padding: 12px 15px;
    background-color: #C99700;
    color: #000;
    border: none;
    font-size: 16px;
    font-weight: 600;
    text-align: left;
    cursor: pointer;
    font-family: Verdana, Geneva, sans-serif;
}
.quick-links-content {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
}
.quick-links-content.active {
    max-height: 300px;
}
.quick-links-content ul {
    list-style: none;
    padding: 15px;
}
.quick-links-content li {
    margin-bottom: 10px;
}
.quick-links-content a {
    color: #996600;
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
}
.footer {
    background-color: #C99700;
    padding: 15px;
    text-align: center;
}
.footer-container {
    color: #000;
}
.footer-container p {
    font-size: 12px;
    margin-bottom: 10px;
}
.footer-link {
    color: #000;
    text-decoration: none;
    font-size: 12px;
    font-weight: 600;
}
.tile-group {
    display: none;
    margin-bottom: 20px;
}
.tile-group.active {
    display: block;
    border: 2px solid #C99700;
    box-sizing: border-box;
    padding: 5px;
}
.resources h2 {
    font-size: 20px;
    font-weight: 700;
    color: #000;
    margin-bottom: 15px;
}
.accordion-toggle:checked+.accordion-header::after {
    transform: rotate(180deg);
}
.accordion-toggle:checked+.accordion-header {
    background-color: #996600;
    color: #fff;
}
.accordion-toggle:checked~.accordion-content {
    max-height: 800px;
    padding: 15px;
}
.accordion-content p {
    font-size: 14px;
    color: #000;
    margin-bottom: 10px;
}
.accordion-content li {
    font-size: 14px;
    color: #000;
    margin-bottom: 5px;
}
.accordion-content a {
    color: #996600;
    text-decoration: none;
    font-weight: 600;
}
.contact-info h3 {
    font-size: 24px;
    color: #000;
    background-color: #C99700;
    padding: 10px;
    margin-bottom: 15px;
}
.contact-list li {
    margin-bottom: 10px;
    padding-left: 5px;
}
.contact-info p {
    margin-bottom: 10px;
}
.contact-info a {
    color: #996600;
    text-decoration: underline;
}
#status-message {
    position: absolute;
    clip-path: inset(100%);
    width: 1px;
    height: 1px;
    overflow: hidden;
    visibility: hidden;
    opacity: 0;
    white-space: nowrap;
}
/* Media queries for responsive design */
@media (min-width: 768px) {
    .header-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 15px 20px;
    }
    .nav-toggle {
        display: none;
    }
    .header-nav {
        display: block;
        position: static;
        box-shadow: none;
        background-color: transparent;
    }
    .header-nav ul {
        display: flex;
    }
    .header-nav li {
        padding: 0;
        margin-right: 20px;
    }
    .main {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 20px;
    }
    .tile-grid {
        grid-template-columns: repeat(5, 1fr);
    }
    .tile-row {
        grid-template-columns: repeat(6, 1fr);
    }
    .quick-links {
        height: fit-content;
    }
    .quick-links-toggle {
        display: none;
    }
    .quick-links-content {
        max-height: none;
        padding: 20px;
    }
    .quick-links-content a {
        font-size: 16px;
    }
    .footer {
        padding: 20px;
    }
    .footer-container {
        display: flex;
        justify-content: space-between;
        max-width: 1200px;
        margin: 0 auto;
    }
}
.sub-add-text {
    text-align: center;
    margin-bottom: 15px;
}
.sub-add-text div {
    text-align: left;
    max-width: 600px;
    margin: 0 auto;
}
.sub-link-list {
    list-style: none;
    padding: 10px;
    margin-bottom: 20px;
}
.sub-link-list li {
    margin-bottom: 10px;
}
.sub-link-list a {
    color: #000000;
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    display: block;
    padding: 10px;
    background-color: #ffffff;
    border: 1px solid #bdbdbd;
    border-radius: 5px;
    transition: background-color 0.3s ease;
}
.sub-link-list a:hover,
.sub-link-list a:focus {
    background-color: #f0f0f0;
}
'''

# Global variables for application state
parsed_data = None
temp_dir = None
photos = []
active_labels = [] # Track active labels to prevent updating destroyed widgets
sub_buttons = {}
add_text = None
image_cache = {}

# Parses HTML content to extract title, images, and tile information
def parse_page(html_content):
    try:
        soup = BeautifulSoup(html_content, 'lxml')
        title_div = soup.find('div', class_='sectiontext')
        title = title_div.text.strip() if title_div else 'Untitled'
        top_img = soup.find('img', class_='w3-image w3-width-100')
        top_img_src = top_img['src'] if top_img else None
        welcome = ''
        location_text = ''
        tiles = []
        for child in soup.find_all('div', class_='child w3-card tile'):
            a = child.find('a')
            if a:
                href = a.get('href', '#')
                img = a.find('img')  # Changed to find any <img> tag within the <a> element
                icon_src = img['src'] if img else ''
                tile_text_div = a.find('div', class_='tiletext')
                text = tile_text_div.text.strip() if tile_text_div else ''
                tiles.append({'text': text, 'icon': icon_src, 'href': href, 'sub_tiles': None, 'sub_add_text': '', 'use_direct': False, 'mode': 'tiles'})
        is_list_page = False
        if not tiles:
            header = soup.find('div', class_='exlheader')
            if header:
                title_b = header.find('b')
                title = title_b.text.strip() if title_b else 'Untitled'
                top_img_src = None
                links = soup.find_all('a', class_='exllink')
                for a in links:
                    text = a.text.strip()
                    if text:
                        href = a.get('href', '#')
                        tiles.append({'text': text, 'icon': None, 'href': href, 'sub_tiles': None, 'sub_add_text': '', 'use_direct': False, 'mode': 'list'})
                is_list_page = True
        return {'title': title, 'welcome': welcome, 'location': location_text, 'top_img': top_img_src, 'tiles': tiles, 'is_list_page': is_list_page}
    except Exception as e:
        messagebox.showerror("Parsing Error", f"Error parsing HTML: {str(e)}")
        print(f"Parsing error: {str(e)}")
        return None

# Clears all widgets from a given frame
def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()
    global active_labels
    active_labels = [] # Clear active labels when clearing frame

# Downloads an image from a URL and caches it locally
def download_image(url):
    if not url:
        return None
    if url in image_cache:
        return image_cache[url]
    try:
        filename = os.path.basename(url)
        local_path = os.path.join(temp_dir, filename)
        urlretrieve(url, local_path)
        image_cache[url] = local_path
        return local_path
    except Exception as e:
        print(f"Image download error: {str(e)}")
        return None

# Loads and resizes an image asynchronously for display
def load_image_async(local_path, label, size):
    try:
        img = Image.open(local_path)
        if size is None:
            size = img.size
        resized_img = img.resize(size, Image.NEAREST)
        photo = ImageTk.PhotoImage(resized_img)
        photos.append(photo)
        if label.winfo_exists(): # Check if label still exists
            root.after(0, lambda: label.config(image=photo) if label.winfo_exists() else None)
    except Exception as e:
        print(f"Image load error: {str(e)}")
        messagebox.showwarning("Image Error", f"Failed to load image: {str(e)}")

# Builds a preview of the parsed HTML content in the GUI
def build_preview(parsed):
    try:
        clear_frame(preview_frame)
        if not parsed:
            return
        title_label = ttk.Label(preview_frame, text=parsed['title'], font=('Verdana', 12, 'bold'))
        title_label.pack(pady=5)
        intro_frame = ttk.Frame(preview_frame)
        intro_frame.pack(fill=tk.X, pady=2)
        if parsed['top_img']:
            local_path = download_image(parsed['top_img'])
            if local_path:
                img_label = ttk.Label(intro_frame)
                img_label.pack()
                active_labels.append(img_label) # Track label
                threading.Thread(target=load_image_async, args=(local_path, img_label, None)).start()
        additional_text = add_text.get("1.0", tk.END).strip()
        if additional_text:
            add_lines = additional_text.split('\n')
            for line in add_lines:
                if line.strip():
                    add_label = ttk.Label(intro_frame, text=line.strip(), justify=tk.LEFT, wraplength=300, font=('Verdana', 8))
                    add_label.pack(anchor=tk.W)
        if parsed['is_list_page']:
            list_frame = ttk.Frame(preview_frame)
            list_frame.pack(fill=tk.X, padx=2, pady=2)
            for tile in parsed['tiles']:
                sub_text = ttk.Label(list_frame, text=tile['text'], font=('Verdana', 6), wraplength=250)
                sub_text.pack(anchor=tk.W, pady=1)
        else:
            tiles_frame = ttk.Frame(preview_frame)
            tiles_frame.pack(fill=tk.BOTH, expand=True)
            row = 0
            col = 0
            sub_frames = {}
            for tile in parsed['tiles']:
                tile_frame = ttk.Frame(tiles_frame, borderwidth=2, relief='raised', width=80, height=90)
                tile_frame.grid(row=row, column=col, padx=2, pady=2, sticky=tk.NSEW)
                if tile['icon']:
                    local_path = download_image(tile['icon'])
                    if local_path:
                        icon_label = ttk.Label(tile_frame)
                        icon_label.pack()
                        active_labels.append(icon_label) # Track label
                        threading.Thread(target=load_image_async, args=(local_path, icon_label, (35, 35))).start()
                text_label = ttk.Label(tile_frame, text=tile['text'], font=('Verdana', 7, 'bold'), wraplength=70)
                text_label.pack()
                if tile['href'].startswith('campusm://pocketguide?pg_code=') and not tile['use_direct']:
                    sub_frame = ttk.Frame(preview_frame, borderwidth=2, relief='sunken')
                    sub_frames[tile['text']] = sub_frame
                    if tile['mode'] == 'text_only' or tile['sub_tiles']:
                        if tile.get('sub_add_text', ''):
                            sub_add_label = ttk.Label(sub_frame, text=tile['sub_add_text'], justify=tk.LEFT, wraplength=300, font=('Verdana', 8))
                            sub_add_label.pack(anchor=tk.CENTER, pady=2)
                        if tile['sub_tiles']: # Only add sub-tiles if not text_only (which sets sub_tiles=None)
                            if tile['mode'] == 'list':
                                list_frame = ttk.Frame(sub_frame)
                                list_frame.pack(fill=tk.X, padx=2, pady=2)
                                for sub_tile in tile['sub_tiles']:
                                    sub_text = ttk.Label(list_frame, text=sub_tile['text'], font=('Verdana', 6), wraplength=250)
                                    sub_text.pack(anchor=tk.W, pady=1)
                            else:
                                sub_tiles_frame = ttk.Frame(sub_frame)
                                sub_tiles_frame.pack(fill=tk.X, padx=2, pady=2)
                                sub_row_frame = None
                                sub_col = 0
                                for sub_tile in tile['sub_tiles']:
                                    if sub_col == 0:
                                        sub_row_frame = ttk.Frame(sub_tiles_frame)
                                        sub_row_frame.pack(fill=tk.X, pady=1)
                                    sub_tile_frame = ttk.Frame(sub_row_frame, borderwidth=1, relief='ridge', width=60, height=70)
                                    sub_tile_frame.pack(side=tk.LEFT, padx=2, pady=2, expand=True, fill=tk.X)
                                    if sub_tile['icon']:
                                        sub_local = download_image(sub_tile['icon'])
                                        if sub_local:
                                            sub_icon = ttk.Label(sub_tile_frame)
                                            sub_icon.pack()
                                            active_labels.append(sub_icon) # Track label
                                            threading.Thread(target=load_image_async, args=(sub_local, sub_icon, (25, 25))).start()
                                    sub_text = ttk.Label(sub_tile_frame, text=sub_tile['text'], font=('Verdana', 6), wraplength=50)
                                    sub_text.pack()
                                    sub_col += 1
                                    if sub_col >= 3:
                                        sub_col = 0
                    def toggle(sub_f=sub_frame):
                        if sub_f.winfo_ismapped():
                            sub_f.pack_forget()
                        else:
                            sub_f.pack(after=tiles_frame, fill=tk.X, pady=2)
                    tile_frame.bind('<Button-1>', lambda e, s=sub_frame: toggle())
                col += 1
                if col >= 3:
                    col = 0
                    row += 1
            for i in range(row + 1):
                tiles_frame.rowconfigure(i, weight=1)
            for i in range(3):
                tiles_frame.columnconfigure(i, weight=1)
    except Exception as e:
        messagebox.showerror("Preview Error", f"Error building preview: {str(e)}")
        print(f"Build preview error: {str(e)}")

# Builds a template preview with placeholder tiles
def build_template_preview():
    try:
        clear_frame(preview_frame)
        title_label = ttk.Label(preview_frame, text="Template Preview", font=('Verdana', 12, 'bold'))
        title_label.pack(pady=5)
        intro_frame = ttk.Frame(preview_frame)
        intro_frame.pack(fill=tk.X, pady=2)
        add_label = ttk.Label(intro_frame, text="Additional text placeholder", justify=tk.LEFT, wraplength=300, font=('Verdana', 8))
        add_label.pack(anchor=tk.W)
        tiles_frame = ttk.Frame(preview_frame)
        tiles_frame.pack(fill=tk.BOTH, expand=True)
        placeholder_tiles = [
            {'text': 'Tile 1', 'icon': 'https://portal-na.campusm.exlibrisgroup.com/assets/MonroeCommunityCollege/MonroeCommunityCollege/Icons-from-Campusm/996600-hex-color/Advisor.png'},
            {'text': 'Tile 2', 'icon': 'https://portal-na.campusm.exlibrisgroup.com/assets/MonroeCommunityCollege/MonroeCommunityCollege/Icons-from-Campusm/996600-hex-color/Academics.png'},
            {'text': 'Tile 3', 'icon': 'https://portal-na.campusm.exlibrisgroup.com/assets/MonroeCommunityCollege/MonroeCommunityCollege/Icons-from-Campusm/996600-hex-color/Events.png'},
            {'text': 'Tile 4', 'icon': 'https://portal-na.campusm.exlibrisgroup.com/assets/MonroeCommunityCollege/MonroeCommunityCollege/Icons-from-Campusm/996600-hex-color/Advisor.png'},
            {'text': 'Tile 5', 'icon': 'https://portal-na.campusm.exlibrisgroup.com/assets/MonroeCommunityCollege/MonroeCommunityCollege/Icons-from-Campusm/996600-hex-color/Academics.png'},
            {'text': 'Tile 6', 'icon': 'https://portal-na.campusm.exlibrisgroup.com/assets/MonroeCommunityCollege/MonroeCommunityCollege/Icons-from-Campusm/996600-hex-color/Events.png'},
            {'text': 'Tile 7', 'icon': 'https://portal-na.campusm.exlibrisgroup.com/assets/MonroeCommunityCollege/MonroeCommunityCollege/Icons-from-Campusm/996600-hex-color/Advisor.png'},
            {'text': 'Tile 8', 'icon': 'https://portal-na.campusm.exlibrisgroup.com/assets/MonroeCommunityCollege/MonroeCommunityCollege/Icons-from-Campusm/996600-hex-color/Academics.png'},
            {'text': 'Tile 9', 'icon': 'https://portal-na.campusm.exlibrisgroup.com/assets/MonroeCommunityCollege/MonroeCommunityCollege/Icons-from-Campusm/996600-hex-color/Events.png'},
            {'text': 'Direct Link 1', 'icon': 'https://portal-na.campusm.exlibrisgroup.com/assets/MonroeCommunityCollege/MonroeCommunityCollege/Icons-from-Campusm/996600-hex-color/Advisor.png'},
            {'text': 'Direct Link 2', 'icon': 'https://portal-na.campusm.exlibrisgroup.com/assets/MonroeCommunityCollege/MonroeCommunityCollege/Icons-from-Campusm/996600-hex-color/Academics.png'},
            {'text': 'Direct Link 3', 'icon': 'https://portal-na.campusm.exlibrisgroup.com/assets/MonroeCommunityCollege/MonroeCommunityCollege/Icons-from-Campusm/996600-hex-color/Events.png'},
        ]
        row = 0
        col = 0
        sub_frames = {}
        for i, tile in enumerate(placeholder_tiles):
            tile_frame = ttk.Frame(tiles_frame, borderwidth=2, relief='raised', width=80, height=90)
            tile_frame.grid(row=row, column=col, padx=2, pady=2, sticky=tk.NSEW)
            local_path = download_image(tile['icon'])
            if local_path:
                icon_label = ttk.Label(tile_frame)
                icon_label.pack()
                active_labels.append(icon_label) # Track label
                threading.Thread(target=load_image_async, args=(local_path, icon_label, (35, 35))).start()
            text_label = ttk.Label(tile_frame, text=tile['text'], font=('Verdana', 7, 'bold'), wraplength=70)
            text_label.pack()
            if i < 9:
                sub_frame = ttk.Frame(preview_frame, borderwidth=2, relief='sunken')
                sub_frames[tile['text']] = sub_frame
                sub_tiles_frame = ttk.Frame(sub_frame)
                sub_tiles_frame.pack(fill=tk.X, padx=2, pady=2)
                sub_row_frame = None
                sub_col = 0
                for j in range(4):
                    if sub_col == 0:
                        sub_row_frame = ttk.Frame(sub_tiles_frame)
                        sub_row_frame.pack(fill=tk.X, pady=1)
                    sub_tile_frame = ttk.Frame(sub_row_frame, borderwidth=1, relief='ridge', width=60, height=70)
                    sub_tile_frame.pack(side=tk.LEFT, padx=2, pady=2, expand=True, fill=tk.X)
                    sub_text = ttk.Label(sub_tile_frame, text=f"Sub {j+1}", font=('Verdana', 6), wraplength=50)
                    sub_text.pack()
                    sub_col += 1
                    if sub_col >= 3:
                        sub_col = 0
                def toggle(sub_f=sub_frame):
                    if sub_f.winfo_ismapped():
                        sub_f.pack_forget()
                    else:
                        sub_f.pack(after=tiles_frame, fill=tk.X, pady=2)
                tile_frame.bind('<Button-1>', lambda e, s=sub_frame: toggle())
            col += 1
            if col >= 3:
                col = 0
                row += 1
        for i in range(row + 1):
            tiles_frame.rowconfigure(i, weight=1)
        for i in range(3):
            tiles_frame.columnconfigure(i, weight=1)
    except Exception as e:
        messagebox.showerror("Template Preview Error", f"Error building template preview: {str(e)}")
        print(f"Build template preview error: {str(e)}")

# Checks if all required sub-pages have been uploaded
def check_all_uploaded():
    if parsed_data:
        for tile in parsed_data['tiles']:
            if tile['href'].startswith('campusm://pocketguide?pg_code='):
                if not (tile['use_direct'] or tile['sub_tiles'] is not None or tile['mode'] == 'text_only'):
                    return False
        return True
    return False

# Creates click-based menu for tile options
def create_hover_menu(tile, label, sub_frame):
    def show_menu(event):
        # Hide all other menus and reset their label colors
        for other_tile_text, btns in sub_buttons.items():
            if other_tile_text != tile['text']:
                btns['menu'].unpost()
                other_label = btns['text_btn'].master.winfo_children()[0]
                other_tile = next((t for t in parsed_data['tiles'] if t['text'] == other_tile_text), None)
                if other_tile:
                    other_label.config(foreground="#008000" if other_tile.get('sub_tiles') or other_tile.get('use_direct') or other_tile['mode'] == 'text_only' else "black")
        menu.delete(0, tk.END)
        if tile.get('sub_tiles') is None:
            menu.add_command(label="Upload", command=lambda: start_upload_sub_thread(tile))
            menu.add_command(label="Direct", command=lambda: set_mode(tile, 'direct', None))
            menu.add_command(label="Text Only", command=lambda: set_mode(tile, 'text_only', None))
        else:
            menu.add_command(label="List", command=lambda: set_mode(tile, 'list', None))
            if not tile.get('sub_is_list', False): # Only show Tiles if not a list page
                menu.add_command(label="Tiles", command=lambda: set_mode(tile, 'tiles', None))
            menu.add_command(label="Text Only", command=lambda: set_mode(tile, 'text_only', None))
            menu.add_command(label="Redo", command=lambda t=tile: redo_upload(t))
        # Only change to blue if not green
        if label.cget('foreground') != '#008000':
            label.config(foreground="#0000FF") # Blue when menu is shown
        menu.post(event.x_root, event.y_root)
    def hide_menu(event=None):
        menu.unpost()
        # Revert to green if uploaded or direct or text_only, else black
        label.config(foreground="#008000" if tile.get('sub_tiles') or tile.get('use_direct') or tile['mode'] == 'text_only' else "black")
    menu = tk.Menu(sub_frame, tearoff=0)
    label.bind("<Button-1>", show_menu)
    root.bind("<Button-1>", lambda e: hide_menu() if e.widget != label and e.widget != menu and e.widget not in [sub_buttons[tile['text']]['text_btn']] else None) # Hide on click elsewhere
    menu.bind("<Leave>", hide_menu) # Hide when mouse leaves menu
    menu.bind("<Button-1>", lambda e: hide_menu()) # Hide on menu item click
    return menu

# Handles redo action for sub-page uploads
def redo_upload(tile):
    tile['sub_tiles'] = None
    tile['sub_add_text'] = ''
    tile['use_direct'] = False
    tile['mode'] = 'tiles' # default
    if 'sub_text_widget' in sub_buttons[tile['text']]:
        sub_buttons[tile['text']]['sub_text_widget'].destroy()
        del sub_buttons[tile['text']]['sub_text_widget']
        if 'submit_btn' in sub_buttons[tile['text']]:
            sub_buttons[tile['text']]['submit_btn'].destroy()
            del sub_buttons[tile['text']]['submit_btn']
        sub_buttons[tile['text']]['text_btn']['text'] = 'Add Text'
    # Update label color to black
    label = sub_buttons[tile['text']]['text_btn'].master.winfo_children()[0]
    label.config(foreground="black")
    build_preview(parsed_data)
    if check_all_uploaded():
        export_btn.config(state=tk.NORMAL)
    else:
        export_btn.config(state=tk.DISABLED)

# Sets the mode for a tile (direct, tiles, or list)
def set_mode(tile, mode, _): # Ignore the upload_btn param
    if mode == 'tiles' and tile.get('sub_is_list', False):
        messagebox.showwarning("Invalid Mode", "Submenu (tiles) not available for list-style sub-pages.")
        return
    if mode == 'direct':
        tile['use_direct'] = True
        tile['mode'] = 'direct'
        tile['sub_tiles'] = None
        tile['sub_add_text'] = ''
        if 'sub_text_widget' in sub_buttons[tile['text']]:
            sub_buttons[tile['text']]['sub_text_widget'].destroy()
            del sub_buttons[tile['text']]['sub_text_widget']
            if 'submit_btn' in sub_buttons[tile['text']]:
                sub_buttons[tile['text']]['submit_btn'].destroy()
                del sub_buttons[tile['text']]['submit_btn']
            sub_buttons[tile['text']]['text_btn']['text'] = 'Add Text'
    else:
        tile['use_direct'] = False
        tile['mode'] = mode
        if mode == 'text_only':
            tile['sub_tiles'] = None # Discard any uploaded sub-tiles for text_only
    # Update label color: green if uploaded or direct or text_only, else black
    label = sub_buttons[tile['text']]['text_btn'].master.winfo_children()[0]
    label.config(foreground="#008000" if tile.get('sub_tiles') or tile.get('use_direct') or tile['mode'] == 'text_only' else "black")
    if check_all_uploaded():
        export_btn.config(state=tk.NORMAL)
    else:
        export_btn.config(state=tk.DISABLED)
    build_preview(parsed_data)

# Handles text button for sub-page additional text
def handle_text_button(tile, text_btn):
    if text_btn.cget('text') == 'Redo':
        tile['sub_add_text'] = ''
        text_btn.config(text='Add Text')
        if 'sub_text_widget' in sub_buttons[tile['text']]:
            sub_buttons[tile['text']]['sub_text_widget'].destroy()
            del sub_buttons[tile['text']]['sub_text_widget']
            if 'submit_btn' in sub_buttons[tile['text']]:
                sub_buttons[tile['text']]['submit_btn'].destroy()
                del sub_buttons[tile['text']]['submit_btn']
        build_preview(parsed_data)
        return
    sub_frame = text_btn.master
    if 'sub_text_widget' not in sub_buttons[tile['text']]:
        text_widget = tk.Text(sub_frame, height=2, width=15, font=('Verdana', 8))
        text_widget.pack(side=tk.LEFT, pady=2)
        text_widget.bind("<KeyRelease>", lambda e, t=tile: update_sub_text(t, text_widget.get("1.0", tk.END).strip()))
        submit_btn = ttk.Button(sub_frame, text="Submit", command=lambda tw=text_widget, tb=text_btn, t=tile: submit_text(tw, tb, t))
        submit_btn.pack(side=tk.LEFT, padx=2)
        sub_buttons[tile['text']]['sub_text_widget'] = text_widget
        sub_buttons[tile['text']]['submit_btn'] = submit_btn

# Submits text and hides text widget
def submit_text(text_widget, text_btn, tile):
    text_widget.pack_forget()
    sub_buttons[tile['text']]['submit_btn'].pack_forget()
    text_btn.config(text='Redo')
    build_preview(parsed_data)

# Processes an uploaded HTML file
def process_upload(file_path, is_sub=False, tile=None):
    try:
        with open(file_path, 'r') as f:
            html_content = f.read()
        parsed = parse_page(html_content)
        if not parsed:
            return None
        return parsed
    except Exception as e:
        messagebox.showerror("Parsing Error", f"Error parsing file: {str(e)}")
        print(f"Parsing error: {str(e)}")
        return None

# Handles main page upload in a separate thread
def upload_main_thread(file_path):
    global parsed_data
    parsed_data = process_upload(file_path)
    if not parsed_data:
        return
    root.after(0, lambda: update_gui_after_main_upload())

# Updates GUI after main page upload
def update_gui_after_main_upload():
    for widget in list(inner_frame.winfo_children())[6:]:
        widget.destroy()
    global sub_buttons
    sub_buttons = {}
    labels = []
    internal_tiles = [t for t in parsed_data['tiles'] if t['href'].startswith('campusm://pocketguide?pg_code=')]
    for itile in internal_tiles:
        sub_frame = ttk.Frame(inner_frame)
        sub_frame.pack(pady=2, anchor=tk.W)
        label = ttk.Label(sub_frame, text=f"For {itile['text']}:", font=('Verdana', 7), wraplength=150)
        label.pack(side=tk.LEFT)
        labels.append(label)
        active_labels.append(label) # Track label
        menu = create_hover_menu(itile, label, sub_frame)
        text_btn = ttk.Button(sub_frame, text="Add Text")
        text_btn.pack(side=tk.LEFT, padx=2)
        text_btn.config(command=lambda t=itile, tb=text_btn: handle_text_button(t, tb))
        sub_buttons[itile['text']] = {'menu': menu, 'text_btn': text_btn}
    align_buttons()
    build_preview(parsed_data)
    if check_all_uploaded():
        export_btn.config(state=tk.NORMAL)
    else:
        export_btn.config(state=tk.DISABLED)

# Starts main page upload in a separate thread
def start_upload_main_thread():
    file_path = filedialog.askopenfilename(filetypes=[("HTML files", "*.html")])
    if file_path:
        threading.Thread(target=upload_main_thread, args=(file_path,)).start()

# Starts sub-page upload in a separate thread
def start_upload_sub_thread(tile):
    file_path = filedialog.askopenfilename(filetypes=[("HTML files", "*.html")])
    if file_path:
        threading.Thread(target=upload_sub_thread, args=(file_path, tile)).start()

# Handles sub-page upload in a separate thread
def upload_sub_thread(file_path, tile):
    sub_parsed = process_upload(file_path, is_sub=True, tile=tile)
    if not sub_parsed:
        return
    root.after(0, lambda: update_gui_after_sub_upload(tile, sub_parsed))

# Updates GUI after sub-page upload
def update_gui_after_sub_upload(tile, sub_parsed):
    tile['sub_tiles'] = sub_parsed['tiles']
    tile['sub_is_list'] = sub_parsed['is_list_page']
    if tile['sub_is_list']:
        set_mode(tile, 'list', None)
    else:
        set_mode(tile, 'tiles', None)
    # Update label color to green
    label = sub_buttons[tile['text']]['text_btn'].master.winfo_children()[0]
    label.config(foreground="#008000")
    build_preview(parsed_data)
    if check_all_uploaded():
        export_btn.config(state=tk.NORMAL)

# Updates sub-tile additional text
def update_sub_text(tile, text):
    tile['sub_add_text'] = text

# Aligns buttons and labels for consistent UI appearance
def align_buttons():
    if not sub_buttons:
        return
    labels = []
    for key, btns in sub_buttons.items():
        sub_frame = btns['text_btn'].master
        label = sub_frame.winfo_children()[0]
        labels.append(label)
    if labels:
        max_label_len = max(len(label.cget('text').replace('\n', '')) for label in labels)
        for label in labels:
            label.config(width=max_label_len // 2 + 1, anchor=tk.W)

# Exports the parsed data to an ADA-compliant HTML file
def export():
    try:
        if not parsed_data:
            return
        soup = BeautifulSoup(template_html, 'lxml')
        soup.title.string = parsed_data['title']
        header_title = soup.find('span', class_='header-title')
        if header_title:
            header_title.string = parsed_data['title']
        intro = soup.find('section', class_='intro')
        if parsed_data['top_img']:
            img_tag = soup.new_tag('img', src=parsed_data['top_img'], alt=parsed_data['title'], style="width:100%;")
            intro.append(img_tag)
        ada = soup.find('section', class_='ada-info')
        additional_text = add_text.get("1.0", tk.END).rstrip('\n')
        if additional_text:
            add_div = soup.new_tag('div', style="max-width:600px; margin:0 auto; text-align:left;")
            add_lines = additional_text.split('\n')
            for line in add_lines:
                p = soup.new_tag('p')
                if line.strip(): # Non-empty lines
                    p.string = line
                else: # Blank lines
                    p.append('\xa0') # Use non-breaking space for proper rendering
                add_div.append(p)
            ada.append(add_div)
        nav_section = soup.find('section', class_='navigation-tiles')
        for child in list(nav_section.children):
            child.extract()
        if parsed_data['is_list_page']:
            ul = soup.new_tag('ul', **{'class': 'sub-link-list', 'role': 'list'})
            for tile in parsed_data['tiles']:
                li = soup.new_tag('li')
                a = soup.new_tag('a', href=tile['href'], **{'class': 'tile-link', 'aria-label': tile['text'], 'tabindex': '0'})
                a.string = tile['text']
                li.append(a)
                ul.append(li)
            nav_section.append(ul)
        else:
            tile_count = 0
            row_div = None
            section_counter = {}
            for tile in parsed_data['tiles']:
                if tile_count % 3 == 0:
                    row_div = soup.new_tag('div', **{'class': 'tile-row'})
                    nav_section.append(row_div)
                section_id_base = tile['text'].lower().replace(' ', '-')
                section_counter[section_id_base] = section_counter.get(section_id_base, 0) + 1
                section_id = f"{section_id_base}-{section_counter[section_id_base]}"
                tile_div = soup.new_tag('div', **{'class': 'tile'})
                if tile['icon']:
                    icon_div = soup.new_tag('div', **{'class': 'tile-icon'})
                    img = soup.new_tag('img', src=tile['icon'], alt="")
                    icon_div.append(img)
                    tile_div.append(icon_div)
                text_div = soup.new_tag('div', **{'class': 'tile-text'})
                text_div.string = tile['text']
                tile_div.append(text_div)
                if tile['href'].startswith('campusm://pocketguide?pg_code=') and not tile['use_direct'] and (tile['sub_tiles'] or tile['mode'] == 'text_only'):
                    button = soup.new_tag('button', onclick=f"toggleSection('{section_id}', this)", onkeydown=f"handleKeydown(event, '{section_id}', this)", **{'data-section': section_id, 'tabindex': '0', 'aria-label': tile['text'], 'aria-expanded': 'false', 'aria-controls': section_id, 'class': 'tile-link navigation-tile'})
                    button.append(tile_div)
                    row_div.append(button)
                    sub_sec = soup.new_tag('section', id=section_id, **{'class': 'tile-group'})
                    container = soup.new_tag('div', **{'class': 'tile-group-container'})
                    h3 = soup.new_tag('h3')
                    h3.string = tile['text']
                    container.append(h3)
                    if tile['sub_add_text']:
                        sub_add_div = soup.new_tag('div', **{'class': 'sub-add-text'})
                        inner_div = soup.new_tag('div')
                        sub_add_lines = tile['sub_add_text'].split('\n')
                        for line in sub_add_lines:
                            p = soup.new_tag('p')
                            if line.strip(): # Non-empty lines
                                p.string = line
                            else: # Blank lines
                                p.append('\xa0') # Use non-breaking space for proper rendering
                            inner_div.append(p)
                        sub_add_div.append(inner_div)
                        container.append(sub_add_div)
                    if tile['sub_tiles']: # Only add sub-tiles if not text_only (which sets sub_tiles=None)
                        if tile['mode'] == 'list':
                            ul = soup.new_tag('ul', **{'class': 'sub-link-list', 'role': 'list'})
                            for sub in tile['sub_tiles']:
                                li = soup.new_tag('li')
                                sub_a = soup.new_tag('a', href=sub['href'], **{'class': 'tile-link', 'aria-label': sub['text'], 'tabindex': '0'})
                                sub_a.string = sub['text']
                                li.append(sub_a)
                                ul.append(li)
                            container.append(ul)
                        else:
                            grid = soup.new_tag('div', **{'class': 'tile-grid', 'role': 'list'})
                            for sub in tile['sub_tiles']:
                                sub_a = soup.new_tag('a', href=sub['href'], **{'class': 'tile-link', 'aria-label': sub['text'], 'tabindex': '0'})
                                sub_tile_div = soup.new_tag('div', **{'class': 'tile', 'role': 'listitem'})
                                if sub['icon']:
                                    sub_icon_div = soup.new_tag('div', **{'class': 'tile-icon'})
                                    sub_img = soup.new_tag('img', src=sub['icon'], alt="")
                                    sub_icon_div.append(sub_img)
                                    sub_tile_div.append(sub_icon_div)
                                sub_text_div = soup.new_tag('div', **{'class': 'tile-text'})
                                sub_text_div.string = sub['text']
                                sub_tile_div.append(sub_text_div)
                                sub_a.append(sub_tile_div)
                                grid.append(sub_a)
                            container.append(grid)
                    sub_sec.append(container)
                    nav_section.append(sub_sec)
                else:
                    a = soup.new_tag('a', href=tile['href'], **{'class': 'tile-link', 'aria-label': tile['text']})
                    a.append(tile_div)
                    row_div.append(a)
                tile_count += 1
        style_tag = soup.new_tag('style')
        style_tag.string = css_string
        soup.head.append(style_tag)
        css_link = soup.find('link', rel='stylesheet')
        if css_link:
            css_link.extract()
        sanitized_title = parsed_data['title'].replace(' ', '_').replace('/', '_')
        base_filename = f"ADA_{sanitized_title}"
        filename = base_filename + ".html"
        file_path = os.path.join(output_dir, filename)
        counter = 1
        while os.path.exists(file_path):
            filename = f"{base_filename}_{counter}.html"
            file_path = os.path.join(output_dir, filename)
            counter += 1
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        messagebox.showinfo("Export Successful", f"File saved to {file_path}")
    except Exception as e:
        messagebox.showerror("Export Error", f"Error during export: {str(e)}")
        print(f"Export error: {str(e)}")

# Allows user to select output directory
def select_output_dir():
    global output_dir
    dir_path = filedialog.askdirectory()
    if dir_path:
        output_dir = dir_path
        messagebox.showinfo("Directory Selected", f"Output directory set to: {dir_path}")

# Sets up the GUI for the application
root = tk.Tk()
root.title("ADA Page Converter")
root.resizable(True, True)
style = ttk.Style()
style.theme_use('clam')
style.configure('TButton', font=('Verdana', 8), padding=5, background='#C99700', foreground='#000')
style.configure('TLabel', font=('Verdana', 8))
preview_frame = ttk.Frame(root)
preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
inner_frame = ttk.Frame(root)
inner_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
select_dir_btn = ttk.Button(inner_frame, text="Select Output Directory", command=select_output_dir)
select_dir_btn.pack(pady=2, anchor=tk.W)
upload_btn = ttk.Button(inner_frame, text="Upload Non-ADA Page", command=start_upload_main_thread)
upload_btn.pack(pady=2, anchor=tk.W)
export_btn = ttk.Button(inner_frame, text="Export ADA Page", command=export, state=tk.DISABLED)
export_btn.pack(pady=2, anchor=tk.W)
ttk.Label(inner_frame, text="Additional Text (before tiles):").pack(pady=2, anchor=tk.W)
add_text = tk.Text(inner_frame, height=3, width=20, font=('Verdana', 8))
add_text.pack(pady=2, anchor=tk.W)
update_btn = ttk.Button(inner_frame, text="Update Preview", command=lambda: build_preview(parsed_data) if parsed_data else build_template_preview())
update_btn.pack(pady=2, anchor=tk.W)

# Creates temporary directory for image storage
temp_dir = tempfile.mkdtemp()

# Initializes template preview
build_template_preview()

# Cleans up temporary directory on application close
def cleanup():
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Cleanup error: {str(e)}")
    root.destroy()

root.protocol("WM_DELETE_WINDOW", cleanup)
root.mainloop()