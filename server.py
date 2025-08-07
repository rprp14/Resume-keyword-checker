from flask import Flask, request, jsonify, send_from_directory, send_file
from PyPDF2 import PdfReader
import pytesseract
from PIL import Image
import os
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
import openai

# Replace with your actual API key
openai.api_key = 'your_openai_api_key_here'

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

# Role-based keyword database
keywords = {
    "Data Scientist": ["python", "pandas", "numpy", "machine learning", "statistics"],
    "Web Developer": ["html", "css", "javascript", "react", "django", "node.js"],
    "Android Developer": ["java", "kotlin", "android studio", "xml", "firebase"],
    "AI Engineer": ["deep learning", "tensorflow", "keras", "pytorch", "nlp"],
    "DevOps Engineer": ["docker", "kubernetes", "jenkins", "aws", "linux"],
    "Cybersecurity Analyst": ["penetration testing", "firewall", "vulnerability", "encryption"],
    "Cloud Engineer": ["aws", "azure", "gcp", "cloudformation", "terraform"]
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text(file_path):
    ext = file_path.rsplit('.', 1)[1].lower()
    text = ''
    if ext == 'pdf':
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
        except:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text()
    else:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
    return text.lower()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/style.css')
def style():
    return send_from_directory('.', 'style.css')

@app.route('/script.js')
def script():
    return send_from_directory('.', 'script.js')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files or 'job_role' not in request.form:
        return jsonify({'error': 'File or job role missing'}), 400

    file = request.files['file']
    job_role = request.form['job_role']
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        resume_text = extract_text(filepath)
        role_keywords = keywords.get(job_role, [])
        
        found = [word for word in role_keywords if word.lower() in resume_text]
        missing = [word for word in role_keywords if word.lower() not in resume_text]

        score = int((len(found) / len(role_keywords)) * 100) if role_keywords else 0

        os.remove(filepath)

        return jsonify({
            'found': found,
            'missing': missing,
            'score': score,
            'resume_text': resume_text
        })
    return jsonify({'error': 'Invalid file type'}), 400

@app.route("/ai_suggestions", methods=["POST"])
def ai_suggestions():
    resume_text = request.json.get("resume_text", "")

    prompt = f"""
    Analyze the following resume text and:
    - Summarize it in 2-3 lines.
    - Suggest 3 improvements.
    - Suggest 3 alternate job roles.

    Resume:
    {resume_text}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response['choices'][0]['message']['content']
        return jsonify({"ai_suggestions": answer})
    except Exception as e:
        return jsonify({"ai_suggestions": "Error: " + str(e)})

@app.route("/download_report", methods=["POST"])
def download_report():
    data = request.json
    matched = data.get("matched", [])
    missing = data.get("missing", [])
    score = data.get("score", 0)
    suggestions = data.get("suggestions", "")

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "📄 Resume Analysis Report")

    y = 770
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"ATS Score: {score}/100")

    y -= 30
    c.drawString(50, y, "✅ Matched Keywords:")
    for word in matched:
        y -= 15
        c.drawString(70, y, f"- {word}")

    y -= 25
    c.drawString(50, y, "❌ Missing Keywords:")
    for word in missing:
        y -= 15
        c.drawString(70, y, f"- {word}")

    y -= 25
    c.drawString(50, y, "💡 AI Suggestions:")
    for line in suggestions.split('\n'):
        y -= 15
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = 800
        c.drawString(70, y, line.strip())

    c.showPage()
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="resume_report.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
