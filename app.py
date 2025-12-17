"""
Flask Web Application for AI Dance Choreography
CPU-optimized MVP for 8GB RAM systems
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import time
from datetime import datetime
import traceback

from audio_processor import AudioProcessor
from generator import DanceGenerator
from bvh_export import BVHExporter

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav', 'ogg', 'm4a'}

# Create folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Initialize components
audio_processor = AudioProcessor(target_fps=60)
dance_generator = None  # Lazy load to save memory
bvh_exporter = BVHExporter(fps=60)

print("\n" + "="*60)
print("🎭 AI Dance Choreography System - MVP")
print("="*60)
print(f"Mode: CPU-only (8GB RAM optimized)")
print(f"Max audio duration: 30 seconds")
print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
print(f"Output folder: {app.config['OUTPUT_FOLDER']}")
print("="*60 + "\n")


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_generator():
    """Lazy load generator to save memory"""
    global dance_generator
    if dance_generator is None:
        print("🔄 Loading dance generator (first time)...")
        dance_generator = DanceGenerator()
        dance_generator.load_model("models/baseline")  # Load baseline model
    return dance_generator


@app.route('/')
def index():
    """Serve main web page"""
    return send_from_directory('static', 'index.html')


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'mode': 'cpu',
        'max_duration': 30,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/upload', methods=['POST'])
def upload_audio():
    """Upload audio file and return file info"""
    try:
        # Check if file is in request
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed: {app.config["ALLOWED_EXTENSIONS"]}'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        # Get audio info
        try:
            duration = audio_processor.load_audio(filepath)[0].shape[0] / 48000
            bpm = audio_processor.get_bpm(filepath)
        except Exception as e:
            duration = 0
            bpm = 0
            print(f"Warning: Could not extract audio info: {e}")
        
        print(f"✅ Audio uploaded: {unique_filename}")
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'filepath': filepath,
            'duration': round(duration, 2),
            'bpm': round(bpm, 1)
        })
    
    except Exception as e:
        print(f"❌ Upload error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate', methods=['POST'])
def generate_dance():
    """Generate dance from uploaded audio file"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        style = data.get('style', 'auto')
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Audio file not found'}), 404
        
        print(f"\n{'='*60}")
        print(f"🎵 Starting dance generation...")
        print(f"File: {filename}")
        print(f"Style: {style}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        # Step 1: Extract audio features
        print("Step 1/3: Extracting audio features...")
        features = audio_processor.extract_features(filepath)
        
        # Step 2: Generate dance motion
        print("\nStep 2/3: Generating dance motion...")
        generator = get_generator()
        motion = generator.generate(features, dance_style=style)
        smpl_motion = generator.convert_to_smpl(motion)
        
        # Step 3: Export to BVH
        print("\nStep 3/3: Exporting to BVH...")
        output_filename = filename.rsplit('.', 1)[0] + '_dance.bvh'
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        bvh_exporter.export(
            motion_data=smpl_motion['rotations'],
            translations=smpl_motion['translations'],
            output_path=output_path
        )
        
        generation_time = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"✅ Generation complete!")
        print(f"Time: {generation_time:.1f}s")
        print(f"Output: {output_filename}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'output_filename': output_filename,
            'output_path': output_path,
            'num_frames': motion['num_frames'],
            'duration': round(motion['num_frames'] / motion['fps'], 2),
            'generation_time': round(generation_time, 1),
            'bpm': round(features['tempo'], 1)
        })
    
    except Exception as e:
        print(f"\n❌ Generation error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<filename>', methods=['GET'])
def download_bvh(filename):
    """Download generated BVH file"""
    try:
        filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
    
    except Exception as e:
        print(f"❌ Download error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/preview/<filename>', methods=['GET'])
def preview_motion(filename):
    """Get motion data for 3D preview (JSON format)"""
    try:
        # For MVP, we skip JSON export and just return basic info
        # Full implementation would convert BVH to JSON for Three.js viewer
        
        bvh_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        
        if not os.path.exists(bvh_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Return file info for now
        file_size = os.path.getsize(bvh_path)
        
        return jsonify({
            'filename': filename,
            'size': file_size,
            'format': 'bvh',
            'message': 'Download BVH file and import into Blender/Unity for visualization'
        })
    
    except Exception as e:
        print(f"❌ Preview error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n🚀 Starting Flask server...")
    print("📡 URL: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
