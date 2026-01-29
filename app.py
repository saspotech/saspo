import os
import json
from functools import wraps
from flask import Flask, render_template, Response, url_for, request, redirect, session, flash
from werkzeug.utils import secure_filename
from fpdf import FPDF
from datetime import datetime

app = Flask(__name__)

# ================= CONFIGURATION (ABSOLUTE PATHS FIX) =================
# This fixes [WinError 2] by calculating the exact folder path on your computer/server
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'saspoworld-super-secret-key-2026')
app.config['ADMIN_USERNAME'] = 'saspo'
app.config['ADMIN_PASSWORD'] = 'Password123*' 

# Use os.path.join to build safe paths
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'img')
app.config['LINKS_DB'] = os.path.join(BASE_DIR, 'links.json')
app.config['DATA_FILE'] = os.path.join(BASE_DIR, 'data.json')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'webm'}

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ================= HELPER FUNCTIONS =================

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def load_json_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {} if filename == app.config['DATA_FILE'] else []

def save_json_file(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Restricted Area: Please log in.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def generate_seo(data):
    game_titles = [g.get('title', '') for g in data.get('games', {}).values()]
    course_titles = [c.get('title', '') for c in data.get('courses', [])]
    tool_names = [t.get('title', '') for t in data.get('ai_tools', [])]
    
    core_tags = [
        "Saspo", "Saspo World", "Saspo Tech", "Saspotech", 
        "AI", "Generative AI", "VFX", "Visual Effects", 
        "Game Development", "Unreal Engine", "Unity", 
        "Designing", "Creatives", "Immersive Tech", 
        "Kochi", "Kerala", "India", "Startup"
    ]
    
    all_keywords = list(set(core_tags + game_titles + course_titles + tool_names))
    desc = "Saspo World Technologies: A Premier AI & Immersive Tech Studio in Kochi. "
    if game_titles: desc += f"Creators of {', '.join(game_titles[:3])}. "
    if course_titles: desc += f"Specialized training in {', '.join(course_titles[:3])}."
        
    return {"keywords": ", ".join(all_keywords), "description": desc}

# ================= PUBLIC ROUTES =================

@app.route('/')
def index():
    data = load_json_file(app.config['DATA_FILE'])
    links = load_json_file(app.config['LINKS_DB'])
    if not isinstance(links, list): links = []
    seo_data = generate_seo(data)
    return render_template('index.html', 
                         games=data.get('games', {}), 
                         ai_influencers=data.get('ai_influencers', []), 
                         courses=data.get('courses', []), 
                         team=data.get('team', []), 
                         contact=data.get('contact', {}),
                         ai_tools=data.get('ai_tools', []),
                         links=links,
                         seo=seo_data)

# ================= ADMIN ROUTES =================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASSWORD']:
            session['logged_in'] = True
            return redirect(request.args.get('next') or url_for('dashboard'))
        else:
            flash('Access Denied: Invalid Credentials', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    data = load_json_file(app.config['DATA_FILE'])
    json_str = json.dumps(data, indent=4, ensure_ascii=False)
    
    try:
        images = sorted(os.listdir(app.config['UPLOAD_FOLDER']))
    except FileNotFoundError:
        images = []

    saved_links = load_json_file(app.config['LINKS_DB'])
    if not isinstance(saved_links, list): saved_links = []

    usage_map = {}
    for img in images:
        usage_map[img] = (json_str[:json_str.find(img)].count('\n') + 1) if img in json_str else None
    for link in saved_links:
        url = link.get('url', '')
        usage_map[url] = (json_str[:json_str.find(url)].count('\n') + 1) if url in json_str else None
        
    return render_template('dashboard.html', json_data=json_str, images=images, links=saved_links, usage_map=usage_map)

@app.route('/update_data', methods=['POST'])
@login_required
def update_data():
    try:
        new_data = json.loads(request.form.get('json_data'))
        if save_json_file(app.config['DATA_FILE'], new_data):
            flash('Database updated successfully.', 'success')
        else:
            flash('Error writing to file.', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('dashboard'))

@app.route('/upload_file', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files: return redirect(url_for('dashboard'))
    file = request.files['file']
    if file.filename == '': return redirect(url_for('dashboard'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash(f'Uploaded: {filename}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_file/<filename>', methods=['POST'])
@login_required
def delete_file(filename):
    # 1. Sanitize the input filename
    safe_name = secure_filename(filename)
    
    # 2. Prevent deleting SYSTEM files (GIFs and logo.png)
    if safe_name.lower().endswith('.gif') or safe_name == 'logo.png':
        flash(f'System Protected: {safe_name}', 'error')
        return redirect(url_for('dashboard'))
        
    # 3. Check usage in JSON
    if safe_name in json.dumps(load_json_file(app.config['DATA_FILE'])):
        flash(f'Cannot delete {safe_name}: In use.', 'error')
        return redirect(url_for('dashboard'))

    # 4. Construct Absolute Path (Fixes WinError 2)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)

    # 5. Verify existence before deletion
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            flash(f'Deleted: {safe_name}', 'success')
        except Exception as e:
            flash(f'System Error: {str(e)}', 'error')
    else:
        # If secure_filename didn't find it, try exact match (for spaces)
        # Only allow simple file names to avoid directory traversal
        if filename != safe_name and not ('/' in filename or '\\' in filename):
             raw_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
             if os.path.exists(raw_path):
                 try:
                     os.remove(raw_path)
                     flash(f'Deleted: {filename}', 'success')
                 except Exception as e:
                     flash(f'System Error: {str(e)}', 'error')
             else:
                 flash(f'File Not Found: {filename}', 'error')
        else:
            flash(f'File Not Found: {safe_name}', 'error')

    return redirect(url_for('dashboard'))

@app.route('/add_link', methods=['POST'])
@login_required
def add_link():
    title = request.form.get('title')
    url = request.form.get('url')
    if title and url:
        links = load_json_file(app.config['LINKS_DB'])
        if not isinstance(links, list): links = []
        if not any(l['url'] == url for l in links):
            links.append({'title': title, 'url': url})
            save_json_file(app.config['LINKS_DB'], links)
            flash('Link added.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_link', methods=['POST'])
@login_required
def delete_link():
    url = request.form.get('url')
    if url in json.dumps(load_json_file(app.config['DATA_FILE'])):
        flash('Cannot delete link: In use.', 'error')
        return redirect(url_for('dashboard'))
    links = load_json_file(app.config['LINKS_DB'])
    new_links = [l for l in links if l['url'] != url]
    save_json_file(app.config['LINKS_DB'], new_links)
    flash('Link removed.', 'success')
    return redirect(url_for('dashboard'))

# --- BOOK-STYLE PDF GENERATOR (Robust against Emojis) ---
class BookPDF(FPDF):
    def safe_text(self, text):
        return text.encode('latin-1', 'replace').decode('latin-1')

    def header(self):
        if self.page_no() == 1: return
        self.set_font('Times', 'I', 9)
        self.set_text_color(150)
        self.cell(0, 10, 'Saspo World Technologies | Administrator Manual', 0, 0, 'R')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Times', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'{self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('Times', 'B', 16)
        self.set_text_color(30, 30, 30)
        self.cell(0, 10, self.safe_text(label.upper()), 0, 1, 'L')
        self.set_draw_color(0, 242, 234) # Cyan
        self.set_line_width(0.5)
        self.line(self.get_x(), self.get_y(), 200, self.get_y())
        self.ln(8)

    def chapter_body(self, body):
        self.set_font('Times', '', 11)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 6, self.safe_text(body))
        self.ln(4)

    def sub_heading(self, label):
        self.ln(2)
        self.set_font('Times', 'B', 12)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, self.safe_text(label), 0, 1)

    def code_block(self, code):
        self.set_font('Courier', '', 9)
        self.set_text_color(0, 100, 0)
        self.set_fill_color(248, 248, 248)
        self.set_x(15) 
        self.multi_cell(180, 5, self.safe_text(code), 0, 'L', True)
        self.ln(4)

@app.route('/download_manual')
@login_required
def download_manual():
    pdf = BookPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(15, 20, 15)
    
    # --- PAGE 1: TITLE PAGE ---
    pdf.add_page()
    pdf.ln(60)
    pdf.set_font('Times', 'B', 36)
    pdf.cell(0, 15, 'OPERATIONS', 0, 1, 'C')
    pdf.cell(0, 15, 'MANUAL', 0, 1, 'C')
    
    pdf.ln(20)
    pdf.set_font('Times', '', 14)
    pdf.cell(0, 10, 'ADMINISTRATIVE CONTROL PANEL V2.0', 0, 1, 'C')
    
    pdf.ln(60)
    pdf.set_font('Times', 'I', 10)
    pdf.set_text_color(100)
    pdf.cell(0, 10, f'Generated: {datetime.now().strftime("%B %d, %Y")}', 0, 1, 'C')
    pdf.cell(0, 5, 'Saspo World Technologies Pvt. Ltd.', 0, 1, 'C')
    
    # --- PAGE 2: TABLE OF CONTENTS ---
    pdf.add_page()
    pdf.chapter_title('Table of Contents')
    toc = [
        "1.  System Overview",
        "2.  The Dashboard Interface",
        "3.  Homepage & AI Tools",
        "4.  Video Management",
        "5.  Portfolio Schema (Games)",
        "6.  Academy Schema (Courses)",
        "7.  Team & Leadership Schema",
        "8.  Virtual Talent (AI Influencers)",
        "9.  Legal Data (Privacy & Terms)",
        "10. Contact & WhatsApp Redirect Logic"
    ]
    for item in toc:
        pdf.chapter_body(item)
    
    # --- CHAPTER 1 ---
    pdf.add_page()
    pdf.chapter_title('1. System Overview')
    pdf.chapter_body(
        "The Saspo World CMS uses a 'Flat-File Database' architecture. This means there is no complex SQL database to manage. "
        "All website content is stored in a single file named 'data.json'.\n\n"
        "When you edit the website via the Dashboard, you are directly modifying this JSON file. The system includes "
        "automatic error checking to prevent you from saving invalid code that could break the site."
    )

    # --- CHAPTER 2 ---
    pdf.chapter_title('2. The Dashboard Interface')
    pdf.chapter_body(
        "1. SIDEBAR (ASSETS): Manages images/videos. Click a file to copy its name.\n"
        "2. EDITOR (CODE): The raw 'data.json' editor. Use this to update text and links.\n"
        "3. DOCS BUTTON: Downloads this manual."
    )

    # --- CHAPTER 3 ---
    pdf.add_page()
    pdf.chapter_title('3. Homepage & AI Tools')
    pdf.sub_heading("3.1 Hero Section")
    pdf.chapter_body(
        "The main 'Hero' section (the first thing users see) contains the tagline and main buttons. "
        "Currently, the video background and main headline are hardcoded in the template for performance stability. "
        "However, the 'Proprietary AI Tools' section below it is fully editable."
    )
    pdf.sub_heading("3.2 AI Tools")
    pdf.chapter_body(
        "You can add unlimited tools in the 'ai_tools' list. Each tool needs a title, description, link, and icon."
    )
    pdf.code_block(
        '{\n'
        '  "title": "Saspo Script Gen",\n'
        '  "desc": "Automated narrative engine...",\n'
        '  "link": "https://...",\n'
        '  "icon": "Icon"\n'
        '}'
    )

    # --- CHAPTER 4 ---
    pdf.chapter_title('4. Video Management')
    pdf.chapter_body(
        "To keep the website lightweight, we do not upload large video files directly. Instead, we embed YouTube videos."
    )
    pdf.sub_heading("4.1 Adding Videos")
    pdf.chapter_body(
        "1. Go to the Dashboard Header and click 'Add Video Link'.\n"
        "2. Enter an internal Title (e.g., 'Showreel 2026').\n"
        "3. Paste the full YouTube URL.\n"
        "4. The system automatically extracts the Video ID and embeds it on the homepage under the 'Youtube Videos' section."
    )

    # --- CHAPTER 5 ---
    pdf.add_page()
    pdf.chapter_title('5. Portfolio Schema (Games)')
    pdf.chapter_body(
        "Your game portfolio is stored in the 'games' object. Each game has a unique ID (e.g., 'brain-up')."
    )
    pdf.sub_heading("5.1 Special Case: Drone Delivery")
    pdf.chapter_body(
        "The game with the ID 'drone-3d' is special. The website template is coded to display this specific game "
        "as a large, full-width 'Featured Project' at the bottom of the section. Do not change this ID unless "
        "you want to remove the featured highlight."
    )
    pdf.sub_heading("5.2 Data Fields")
    pdf.code_block(
        '- "title": Game Title\n'
        '- "genre": Tag (e.g., "Puzzle")\n'
        '- "img": Filename from sidebar\n'
        '- "link": Download URL or "#"\n'
        '- "description": Short marketing blurb\n'
        '- "features": List of features ["Multiplayer", "Offline"]\n'
        '- "privacy_policy": Policy Object (See Chapter 9)'
    )

    # --- CHAPTER 6 ---
    pdf.chapter_title('6. Academy Schema (Courses)')
    pdf.chapter_body(
        "The '.EDU' section is controlled by the 'courses' list."
    )
    pdf.sub_heading("6.1 Data Structure")
    pdf.code_block(
        '- "title": Course Name\n'
        '- "duration": Time (e.g., "3 Months")\n'
        '- "level": Difficulty\n'
        '- "modules": A list of topics covered.\n'
        '- "tools": Software taught (e.g., "Unreal Engine").'
    )

    # --- CHAPTER 7 ---
    pdf.add_page()
    pdf.chapter_title('7. Team & Leadership')
    pdf.chapter_body(
        "Manage team profiles in the 'team' list. Each member card opens a detailed modal when clicked."
    )
    pdf.sub_heading("7.1 LinkedIn Integration")
    pdf.chapter_body(
        "To add a 'Connect on LinkedIn' button to a team member's profile, simply add a 'socials' object with a 'linkedin' key."
    )
    pdf.code_block(
        '"socials": {\n'
        '    "linkedin": "https://linkedin.com/in/username"\n'
        '}'
    )

    # --- CHAPTER 8 ---
    pdf.chapter_title('8. Virtual Talent')
    pdf.chapter_body(
        "The infinite scrolling marquee of AI Influencers is powered by the 'ai_influencers' list. "
        "For the best visual result, use square images (1:1 aspect ratio)."
    )

    # --- CHAPTER 9 ---
    pdf.chapter_title('9. Legal: Privacy & Terms')
    pdf.chapter_body(
        "The 'Privacy Policy' and 'Terms of Service' modals are generated dynamically. You do not need to write HTML code. "
        "Simply provide the text in the 'privacy' and 'terms' objects inside 'contact'."
    )
    pdf.code_block(
        '"privacy": {\n'
        '  "updated": "Jan 2026",\n'
        '  "intro": "Introduction text...",\n'
        '  "sections": [\n'
        '    {"title": "Data", "content": "Details..."}\n'
        '  ]\n'
        '}'
    )

    # --- CHAPTER 10 ---
    pdf.add_page()
    pdf.chapter_title('10. Contact System & WhatsApp')
    pdf.chapter_body(
        "The website uses a direct-to-WhatsApp inquiry system rather than a traditional email database. "
        "This ensures instant engagement with potential clients."
    )
    pdf.sub_heading("10.1 How it Works")
    pdf.chapter_body(
        "1. A user fills out the 'Start a Project' form on the homepage.\n"
        "2. The website takes their Name and Message.\n"
        "3. It constructs a WhatsApp URL and redirects the user to the WhatsApp app/web interface with the message pre-filled."
    )
    pdf.sub_heading("10.2 Configuration")
    pdf.chapter_body(
        "To change the destination phone number, locate the 'contact' object in the JSON editor and update 'whatsapp_url'."
    )
    
    return Response(pdf.output(dest='S').encode('latin-1', 'replace'), 
                   mimetype='application/pdf',
                   headers={'Content-Disposition': 'attachment;filename=Saspo_Operations_Manual.pdf'})

# ================= SEO ROUTES =================
@app.route('/sitemap.xml')
def sitemap():
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{url_for('index', _external=True)}</loc><lastmod>{date}</lastmod><priority>1.0</priority></url></urlset>"""
    return Response(xml, mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    return Response(f"User-agent: *\nAllow: /\nSitemap: {url_for('sitemap', _external=True)}", mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')