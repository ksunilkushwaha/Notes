from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from PIL import Image
import os
from datetime import datetime
import io

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
UPLOAD_FOLDER = os.path.join('static', 'uploads')

# Initialize database
db = SQLAlchemy(app)

# Define subjects
SUBJECTS = {
    'physics': 'Physics',
    'math': 'Mathematics',
    'computer': 'Computer Science',
    'english': 'English',
    'engineering_drawing': 'Engineering Drawing'
}


# Database Model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_size = db.Column(db.Integer)  # in bytes

    def __repr__(self):
        return f'<Note {self.original_filename}>'


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def compress_image(file, output_folder, filename):
    """Compress and save image"""
    try:
        img = Image.open(file)
        # Convert RGBA to RGB if necessary
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img
        
        # Resize if too large
        img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        
        # Save with compression
        img.save(os.path.join(output_folder, filename), quality=85, optimize=True)
        return True
    except Exception as e:
        print(f"Error compressing image: {e}")
        return False


@app.route('/')
def index():
    """Home page showing all subjects"""
    return render_template('index.html', subjects=SUBJECTS)


@app.route('/subject/<subject>')
def view_subject(subject):
    """View all notes for a specific subject"""
    if subject not in SUBJECTS:
        return redirect(url_for('index'))
    
    # Get all notes for this subject, ordered by newest first
    notes = Note.query.filter_by(subject=subject).order_by(Note.upload_date.desc()).all()
    
    return render_template('gallery.html', 
                         subject=subject,
                         subject_name=SUBJECTS[subject],
                         notes=notes)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Handle file uploads"""
    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        subject = request.form.get('subject')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if subject not in SUBJECTS:
            return jsonify({'error': 'Invalid subject'}), 400
        
        if file and allowed_file(file.filename):
            # Secure the filename
            original_filename = secure_filename(file.filename)
            
            # Create unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            unique_filename = timestamp + original_filename
            
            # Create subject upload folder if not exists
            subject_folder = os.path.join(UPLOAD_FOLDER, subject)
            os.makedirs(subject_folder, exist_ok=True)
            
            filepath = os.path.join(subject_folder, unique_filename)
            
            # Compress and save image
            if compress_image(file, subject_folder, unique_filename):
                # Get file size
                file_size = os.path.getsize(filepath)
                
                # Save to database
                new_note = Note(
                    filename=unique_filename,
                    original_filename=original_filename,
                    subject=subject,
                    file_size=file_size
                )
                db.session.add(new_note)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'File uploaded successfully',
                    'redirect': url_for('view_subject', subject=subject)
                })
            else:
                return jsonify({'error': 'Failed to process image'}), 500
        else:
            return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, BMP'}), 400
    
    return render_template('upload.html', subjects=SUBJECTS)


@app.route('/download/<int:note_id>')
def download(note_id):
    """Download a note"""
    note = Note.query.get(note_id)
    
    if not note:
        return redirect(url_for('index'))
    
    filepath = os.path.join(UPLOAD_FOLDER, note.subject, note.filename)
    
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=note.original_filename)
    else:
        return redirect(url_for('index'))


@app.route('/api/stats')
def get_stats():
    """Get app statistics"""
    total_notes = Note.query.count()
    subject_stats = {}
    
    for subject in SUBJECTS.keys():
        count = Note.query.filter_by(subject=subject).count()
        subject_stats[subject] = count
    
    return jsonify({
        'total_notes': total_notes,
        'subject_stats': subject_stats
    })


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return render_template('500.html'), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='127.0.0.1', port=5000)
