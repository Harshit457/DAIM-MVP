# Quick Start Guide

## Installation (5 minutes)

1. **Open terminal in project folder**:
   ```bash
   cd "d:\Dance model"
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**:
   ```bash
   # Windows
   venv\Scripts\activate
   
   # You should see (venv) in your prompt
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   This will take 2-5 minutes to download and install.
   
   **Note**: MVP doesn't need TensorFlow! Only librosa, Flask, and NumPy.

5. **Verify installation**:
   ```bash
   python -c "import librosa; import flask; import numpy; print('✅ Ready!')"
   ```

## Running the System

1. **Start the server**:
   ```bash
   python app.py
   ```
   
   You should see:
   ```
   🎭 AI Dance Choreography System - MVP
   ====================================
   🚀 Starting Flask server...
   📡 URL: http://localhost:5000
   ```

2. **Open web browser**:
   - Navigate to: `http://localhost:5000`

3. **Use the system**:
   - Drag and drop an MP3 file (or click to browse)
   - Select a dance style (optional)
   - Click "Generate Choreography"
   - Wait 1-3 minutes
   - Download the BVH file

4. **Import into Blender**:
   - Open Blender
   - File → Import → Motion Capture (.bvh)
   - Select your downloaded BVH file
   - Play animation!

## Troubleshooting

### Dependencies won't install
```bash
# Try installing one at a time
pip install librosa==0.10.1
pip install Flask==3.0.0
pip install Flask-CORS==4.0.0
pip install numpy scipy soundfile
```

### Server won't start
- Make sure you're in the virtual environment (see `(venv)` in prompt)
- Make sure port 5000 isn't being used by another program
- Try: `python -m flask run --port 5001`

### Generation fails
- Check audio file is MP3 or WAV
- Check file is less than 30 seconds
- Check file is less than 10MB
- Try a shorter clip

## Need Help?

Check the full [README.md](file:///d:/Dance%20model/README.md) for detailed documentation.
