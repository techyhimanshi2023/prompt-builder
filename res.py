from flask import Flask, request, jsonify
from openai import OpenAI
import os
import PyPDF2
import docx

app = Flask(__name__)

API_KEY = os.environ.get("AIzaSyBokt5-eYbDII5aIKfig36RpHcubs8yuhw")

if not API_KEY:
    raise ValueError("⚠️ OpenAI API key not set in environment variables!")

client = OpenAI(api_key=API_KEY)

def extract_text_from_file(file_path):
    _, file_extension = os.path.splitext(file_path)

    if file_extension == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif file_extension == ".pdf":
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif file_extension == ".docx":
        doc = docx.Document(file_path)
        return " ".join([para.text for para in doc.paragraphs])
    else:
        return None

@app.route('/process', methods=['POST'])
def process_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    task = request.form.get("task", "Summarize")
    length = request.form.get("length", "medium")

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    file_path = os.path.join("uploads", file.filename)
    os.makedirs("uploads", exist_ok=True)
    file.save(file_path)

    text = extract_text_from_file(file_path)
    if not text:
        return jsonify({"error": "Unsupported file type or empty file"}), 400

    prompts = {
        "Summarize": f"Summarize the following text into a {length} summary:\n\n{text}",
        "Analyze Sentiment": f"Analyze the sentiment of this text:\n\n{text}",
        "Extract Keywords": f"Extract the keywords from this text:\n\n{text}",
        "Grammar Check": f"Correct the grammar and improve the clarity of this text:\n\n{text}",
    }

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": prompts[task]}],
            max_tokens=500
        )

        return jsonify({"result": response.choices[0].message.content})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
