// AI Dance Choreography - Frontend Application
// Handles file upload, dance generation, and downloads

const API_URL = 'http://localhost:5000/api';

// State
let uploadedAudio = null;
let selectedStyle = 'auto';
let generatedOutput = null;

// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const audioFile = document.getElementById('audioFile');
const audioInfo = document.getElementById('audioInfo');
const generateBtn = document.getElementById('generateBtn');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultsSection = document.getElementById('resultsSection');
const toast = document.getElementById('toast');

// Style buttons
const styleButtons = document.querySelectorAll('.style-btn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    checkServerHealth();
});

function setupEventListeners() {
    // Upload zone click
    uploadZone.addEventListener('click', () => audioFile.click());
    
    // File input change
    audioFile.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadZone.addEventListener('dragover', handleDragOver);
    uploadZone.addEventListener('dragleave', handleDragLeave);
    uploadZone.addEventListener('drop', handleDrop);
    
    // Style selection
    styleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            styleButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedStyle = btn.dataset.style;
            showToast(`Style selected: ${btn.querySelector('.style-name').textContent}`, 'success');
        });
    });
    
    // Generate button
    generateBtn.addEventListener('click', generateDance);
    
    // Download button (set up after generation)
    document.getElementById('downloadBVH').addEventListener('click', downloadBVH);
}

// Check server health
async function checkServerHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        
        if (data.status === 'ok') {
            console.log('✅ Server connected:', data);
        }
    } catch (error) {
        showToast('⚠️ Cannot connect to server. Make sure Flask is running on port 5000.', 'error');
        console.error('Server health check failed:', error);
    }
}

// Drag and drop handlers
function handleDragOver(e) {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

// File selection handler
function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

// Handle file upload
async function handleFile(file) {
    // Validate file type
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|ogg|m4a)$/i)) {
        showToast('Invalid file type. Please upload MP3, WAV, or OGG file.', 'error');
        return;
    }
    
    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
        showToast('File too large. Maximum size is 10MB.', 'error');
        return;
    }
    
    showToast('Uploading audio file...', 'info');
    
    try {
        const formData = new FormData();
        formData.append('audio', file);
        
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        uploadedAudio = data;
        displayAudioInfo(data);
        generateBtn.disabled = false;
        
        showToast('✅ Audio uploaded successfully!', 'success');
        
    } catch (error) {
        showToast(`Upload failed: ${error.message}`, 'error');
        console.error('Upload error:', error);
    }
}

// Display audio information
function displayAudioInfo(data) {
    document.getElementById('fileName').textContent = data.filename;
    document.getElementById('fileDuration').textContent = `${data.duration}s`;
    document.getElementById('fileBPM').textContent = data.bpm;
    
    audioInfo.style.display = 'block';
}

// Generate dance
async function generateDance() {
    if (!uploadedAudio) {
        showToast('Please upload an audio file first', 'warning');
        return;
    }
    
    // Hide results from previous generation
    resultsSection.style.display = 'none';
    
    // Show progress
    progressContainer.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = 'Starting generation...';
    generateBtn.disabled = true;
    
    try {
        // Simulate progress updates
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                progressFill.style.width = `${progress}%`;
                
                if (progress <= 30) {
                    progressText.textContent = 'Extracting audio features...';
                } else if (progress <= 70) {
                    progressText.textContent = 'Generating dance motion...';
                } else {
                    progressText.textContent = 'Exporting to BVH format...';
                }
            }
        }, 1000);
        
        const response = await fetch(`${API_URL}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: uploadedAudio.filename,
                style: selectedStyle
            })
        });
        
        clearInterval(progressInterval);
        
        if (!response.ok) {
            throw new Error(`Generation failed: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Complete progress
        progressFill.style.width = '100%';
        progressText.textContent = 'Generation complete!';
        
        setTimeout(() => {
            progressContainer.style.display = 'none';
            displayResults(data);
        }, 1000);
        
        generatedOutput = data;
        showToast('✅ Dance generated successfully!', 'success');
        
    } catch (error) {
        progressContainer.style.display = 'none';
        showToast(`Generation failed: ${error.message}`, 'error');
        console.error('Generation error:', error);
        generateBtn.disabled = false;
    }
}

// Display generation results
function displayResults(data) {
    document.getElementById('resultFrames').textContent = data.num_frames;
    document.getElementById('resultDuration').textContent = `${data.duration}s`;
    document.getElementById('resultTime').textContent = `${data.generation_time}s`;
    
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    // Re-enable generate button
    generateBtn.disabled = false;
}

// Download BVH file
async function downloadBVH() {
    if (!generatedOutput) {
        showToast('No dance generated to download', 'warning');
        return;
    }
    
    try {
        showToast('Downloading BVH file...', 'info');
        
        const response = await fetch(`${API_URL}/download/${generatedOutput.output_filename}`);
        
        if (!response.ok) {
            throw new Error(`Download failed: ${response.statusText}`);
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = generatedOutput.output_filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showToast('✅ Download complete!', 'success');
        
    } catch (error) {
        showToast(`Download failed: ${error.message}`, 'error');
        console.error('Download error:', error);
    }
}

// Toast notification
function showToast(message, type = 'info') {
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Spacebar to generate (if file uploaded)
    if (e.code === 'Space' && !generateBtn.disabled && document.activeElement === document.body) {
        e.preventDefault();
        generateDance();
    }
});

console.log('🎭 AI Dance Choreographer - Frontend Loaded');
console.log('Upload audio → Select style → Generate → Download BVH');
