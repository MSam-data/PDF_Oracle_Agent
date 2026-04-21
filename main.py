import os
from flask import Flask, render_template, request, jsonify
from pdf_engine import PDFOracleEngine
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Global instance of our engine
oracle = PDFOracleEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    """Endpoint for the UI to check if the AI is ready."""
    message = oracle.initialize_ai()
    return jsonify({"status": message})

@app.route('/query', methods=['POST'])
def query():
    """Endpoint to process PDF uploads and questions."""
    file = request.files.get('file')
    prompt = request.form.get('prompt')
    
    if not file or not prompt:
        return jsonify({"response": "Please provide both a PDF and a question."}), 400

    # Save the file temporarily
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
    # Process
    text = oracle.extract_text(file_path)
    answer = oracle.query(text, prompt)
    
    # Cleanup: Remove the file after extraction
    if os.path.exists(file_path):
        os.remove(file_path)
        
    return jsonify({"response": answer})

if __name__ == '__main__':
    if not os.path.exists('uploads/'):
        os.makedirs('uploads/')
    # Running on port 5000 by default
    app.run(debug=True)