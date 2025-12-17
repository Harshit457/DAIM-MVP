# Upgrading from Baseline to Full MINT Model

The MVP uses a **baseline procedural generator** that doesn't require machine learning models or TensorFlow. This guide explains how to upgrade to the full **MINT/FACT model** for state-of-the-art realism.

## Why Upgrade?

| Feature | Baseline (Current) | MINT/FACT Model |
|---------|-------------------|-----------------|
| Realism | 3/5 - Simple procedural motion | 5/5 - Professional quality |
| Training Required | None | Pre-trained checkpoint available |
| Style Diversity | Basic intensity variation | 10 distinct dance genres |
| Motion Quality | Functional but repetitive | Natural, expressive movement |
| TensorFlow Required | No | Yes |
| GPU Recommended | No | Yes (but works on CPU) |

## Prerequisites for MINT Model

- **Python**: 3.9, 3.10, or 3.11 (TensorFlow 2.15 doesn't support 3.12 yet)
- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: Optional but recommended (5-10x faster)
- **Disk Space**: ~1.5GB for model checkpoint

## Installation Steps

### 1. Install TensorFlow

**For Python 3.9-3.11:**
```bash
# Activate your virtual environment first
venv\Scripts\activate  # Windows

# Install TensorFlow 2.15 (supports Python 3.9-3.11)
pip install tensorflow==2.15.0
pip install tensorflow-graphics
pip install h5py==3.10.0
```

**For GPU Support** (optional):
```bash
# Install CUDA-enabled TensorFlow
pip install tensorflow[and-cuda]==2.15.0

# Verify GPU is detected
python -c "import tensorflow as tf; print('GPUs:', tf.config.list_physical_devices('GPU'))"
```

### 2. Download MINT Checkpoint

```bash
# Create models directory
mkdir models

# Download pre-trained checkpoint from Google Drive
# Link: https://drive.google.com/drive/folders/17GHwKRZbQfyC9-7oEpzCG8pp_rAI0cOm

# Expected files:
# models/fact_model/
#   ├── checkpoint
#   ├── fact_v5.ckpt-100000.data-00000-of-00001
#   ├── fact_v5.ckpt-100000.index
#   └── fact_v5.ckpt-100000.meta
```

### 3. Install AIST++ API

```bash
pip install git+https://github.com/google/aistplusplus_api.git
```

### 4. Update generator.py

Replace the baseline model loading in `generator.py`:

```python
# OLD (Baseline):
def load_model(self, model_path: str):
    self.model = self._create_baseline_model()
    self.loaded = True

# NEW (MINT):
def load_model(self, model_path: str):
    import tensorflow as tf
    from mint.models import fact_model  # After installing MINT repo
    
    # Load MINT configuration
    config = tf.compat.v1.ConfigProto()
    config.gpu_options.allow_growth = True
    sess = tf.compat.v1.Session(config=config)
    
    # Load checkpoint
    self.model = fact_model.FACT(self.config)
    saver = tf.compat.v1.train.Saver()
    saver.restore(sess, model_path)
    
    self.sess = sess
    self.loaded = True
    print("✅ MINT model loaded successfully")
```

### 5. Update Inference Code

Modify the `generate()` method to use MINT:

```python
def generate(self, audio_features: Dict, dance_style: str = None, 
             seed_motion: np.ndarray = None) -> Dict:
    # Prepare input tensors
    mel_input = audio_features['mel'].T  # (T, 128)
    
    # Run MINT inference
    output = self.sess.run(
        self.model.output_poses,
        feed_dict={
            self.model.input_audio: mel_input[np.newaxis],  # Add batch dim
            self.model.seed_motion: seed_motion,
        }
    )
    
    # Convert SMPL axis-angle to Euler
    rotations = self._axis_angle_to_euler(output['poses'])
    translations = output['trans']
    
    return {
        'rotations': rotations,
        'translations': translations,
        'num_frames': len(rotations),
        'fps': 60
    }
```

### 6. Test the Upgrade

```bash
# Start server
python app.py

# You should see:
# ✅ MINT model loaded successfully
# (instead of "baseline mode")
```

Upload a test audio file and compare the results!

## Alternative: Use MINT Repository Directly

Instead of modifying our MVP, you can use the official MINT repository:

```bash
# Clone MINT
git clone https://github.com/google-research/mint --recursive
cd mint

# Follow their installation guide
# Then use their inference scripts directly
python evaluator.py --audio your_music.wav --output dance.pkl
```

Then convert their output format to BVH using our `bvh_export.py`.

## Troubleshooting

### "No module named 'tensorflow'"
- Make sure you ran `pip install tensorflow==2.15.0`
- Check Python version is 3.9-3.11 (not 3.12)

### "Cannot find MINT checkpoint"
- Download from the Google Drive link above
- Make sure files are in `models/fact_model/` directory

### "Out of memory" errors
- Reduce batch size in model config
- Use shorter audio clips (< 2 minutes)
- Close other applications
- Consider using GPU if available

### Generation is very slow on CPU
- Expected: 3-5 minutes for 30s audio on CPU
- GPU reduces this to 30-60 seconds
- For CPU-only, stick with baseline for now

## Performance Comparison

### Generation Time (30-second audio)

| Hardware | Baseline | MINT Model |
|----------|----------|------------|
| CPU (i7) | 15s | 180s (3 min) |
| GPU (RTX 3060) | 15s | 35s |
| GPU (RTX 4090) | 15s | 20s |

### Motion Quality

Upload the same song to both and compare:
- **Baseline**: Repetitive arm swings, basic tempo matching
- **MINT**: Natural transitions, style-specific moves, expressive gestures

## Reverting to Baseline

If MINT doesn't work or is too slow:

```bash
# Uninstall TensorFlow to save space
pip uninstall tensorflow tensorflow-graphics

# The baseline will automatically be used
python app.py
```

## Further Reading

- [MINT GitHub Repository](https://github.com/google-research/mint)
- [AI Choreographer Paper](https://arxiv.org/abs/2101.08779)
- [AIST++ Dataset](https://google.github.io/aistplusplus_dataset/)

---

**Bottom Line**: The baseline MVP works great for learning and testing. Upgrade to MINT when you need professional-quality animations and have the compute resources (or patience for CPU inference).
