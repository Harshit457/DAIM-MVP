"""
Quick test script to verify the MVP works without TensorFlow
"""

print("=" * 60)
print("Testing AI Dance Choreography MVP (No TensorFlow)")
print("=" * 60)

# Test 1: Import basic modules
print("\n1. Testing imports...")
try:
    import numpy as np
    print("  ✅ NumPy imported")
except ImportError as e:
    print(f"  ❌ NumPy failed: {e}")

try:
    import librosa
    print("  ✅ Librosa imported")
except ImportError as e:
    print(f"  ❌ Librosa failed: {e}")

try:
    from flask import Flask
    print("  ✅ Flask imported")
except ImportError as e:
    print(f"  ❌ Flask failed: {e}")

# Test 2: Import our modules
print("\n2. Testing our modules...")
try:
    from audio_processor import AudioProcessor
    print("  ✅ AudioProcessor imported")
except ImportError as e:
    print(f"  ❌ AudioProcessor failed: {e}")

try:
    from generator import DanceGenerator
    print("  ✅ DanceGenerator imported (no TensorFlow needed!)")
except ImportError as e:
    print(f"  ❌ DanceGenerator failed: {e}")

try:
    from bvh_export import BVHExporter
    print("  ✅ BVHExporter imported")
except ImportError as e:
    print(f"  ❌ BVHExporter failed: {e}")

# Test 3: Test baseline generator
print("\n3. Testing baseline dance generator...")
try:
    gen = DanceGenerator()
    gen.load_model("models/baseline")
    
    # Create dummy features
    dummy_features = {
        'mel': np.random.randn(128, 60),
        'chroma': np.random.randn(12, 60),
        'onset': np.random.rand(60),
        'tempo': 120.0,
        'beats': np.array([0, 15, 30, 45]),
        'duration': 1.0
    }
    
    # Generate motion
    motion = gen.generate(dummy_features)
    print(f"  ✅ Generated {motion['num_frames']} frames")
    print(f"     Shape: {motion['rotations'].shape}")
except Exception as e:
    print(f"  ❌ Generator failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test BVH export
print("\n4. Testing BVH export...")
try:
    from bvh_export import BVHExporter
    
    exporter = BVHExporter(fps=60)
    
    # Create test motion
    test_motion = np.zeros((60, 24, 3))
    test_trans = np.zeros((60, 3))
    test_trans[:, 1] = 1.0  # 1m above ground
    
    # Export
    exporter.export(test_motion, "test_output.bvh", test_trans)
    print("  ✅ BVH export successful")
    
    # Check file exists
    import os
    if os.path.exists("test_output.bvh"):
        size = os.path.getsize("test_output.bvh")
        print(f"     File size: {size} bytes")
        os.remove("test_output.bvh")  # Cleanup
except Exception as e:
    print(f"  ❌ BVH export failed: {e}")

print("\n" + "=" * 60)
print("MVP TEST COMPLETE!")
print("=" * 60)
print("\nIf all tests passed, you can run:")
print("  python app.py")
print("\nThen open: http://localhost:5000")
print("=" * 60)
