"""
Audio Feature Extraction Module
Extracts music features for dance generation using librosa
"""

import librosa
import numpy as np
import soundfile as sf
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')


class AudioProcessor:
    """Process audio files and extract features for dance generation"""
    
    def __init__(self, target_fps: int = 60, sample_rate: int = 48000):
        """
        Args:
            target_fps: Target frames per second for motion data (default: 60)
            sample_rate: Audio sample rate (default: 48000)
        """
        self.target_fps = target_fps
        self.sample_rate = sample_rate
    
    def load_audio(self, audio_path: str, max_duration: float = 30.0) -> Tuple[np.ndarray, int]:
        """
        Load audio file with duration limit
        
        Args:
            audio_path: Path to audio file (MP3, WAV, etc.)
            max_duration: Maximum duration in seconds (default: 30s for MVP)
        
        Returns:
            (audio_data, sample_rate)
        """
        print(f"Loading audio from: {audio_path}")
        
        # Load audio using librosa
        audio, sr = librosa.load(audio_path, sr=self.sample_rate, duration=max_duration)
        
        duration = len(audio) / sr
        print(f"✓ Audio loaded: {duration:.2f}s @ {sr}Hz")
        
        return audio, sr
    
    def extract_features(self, audio_path: str) -> Dict[str, np.ndarray]:
        """
        Extract all audio features needed for dance generation
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Dictionary with extracted features:
            - 'mel': Mel spectrogram (128 x T)
            - 'chroma': Chroma features (12 x T)
            - 'tempo': BPM value
            - 'beats': Beat frame indices
            - 'envelope': Onset strength envelope
        """
        print("\n🎵 Extracting audio features...")
        
        # Load audio
        audio, sr = self.load_audio(audio_path)
        
        # 1. Extract tempo and beats
        tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
        print(f"✓ Tempo: {tempo:.1f} BPM, {len(beats)} beats detected")
        
        # 2. Mel spectrogram (128 bands)
        mel_spec = librosa.feature.melspectrogram(
            y=audio, 
            sr=sr,
            n_mels=128,
            fmax=8000,
            hop_length=512
        )
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        print(f"✓ Mel spectrogram: {mel_spec_db.shape}")
        
        # 3. Chroma features (12-bin pitch class)
        chroma = librosa.feature.chroma_cqt(
            y=audio,
            sr=sr,
            hop_length=512
        )
        print(f"✓ Chroma features: {chroma.shape}")
        
        # 4. Onset strength envelope
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        print(f"✓ Onset envelope: {onset_env.shape}")
        
        # 5. Sync all features to target FPS (60 FPS for motion)
        features_synced = self.sync_to_fps(
            mel=mel_spec_db,
            chroma=chroma,
            onset=onset_env,
            audio_sr=sr,
            hop_length=512
        )
        
        # Add tempo and beats
        features_synced['tempo'] = tempo
        features_synced['beats'] = beats
        features_synced['duration'] = len(audio) / sr
        
        print(f"✓ Features synced to {self.target_fps} FPS")
        print(f"  - Mel: {features_synced['mel'].shape}")
        print(f"  - Duration: {features_synced['duration']:.2f}s")
        
        return features_synced
    
    def sync_to_fps(self, mel: np.ndarray, chroma: np.ndarray, onset: np.ndarray,
                    audio_sr: int, hop_length: int) -> Dict[str, np.ndarray]:
        """
        Synchronize audio features to target FPS
        
        Motion data is at 60 FPS, so we need to resample audio features
        to match frame-by-frame alignment.
        """
        # Calculate current feature frame rate
        feature_fps = audio_sr / hop_length
        
        # Calculate number of target frames
        num_feature_frames = mel.shape[1]
        duration = num_feature_frames / feature_fps
        num_motion_frames = int(duration * self.target_fps)
        
        # Resample each feature to target FPS
        mel_resampled = self._resample_feature(mel, num_motion_frames)
        chroma_resampled = self._resample_feature(chroma, num_motion_frames)
        onset_resampled = self._resample_feature(onset.reshape(1, -1), num_motion_frames)
        
        return {
            'mel': mel_resampled,  # (128, T_motion)
            'chroma': chroma_resampled,  # (12, T_motion)
            'onset': onset_resampled.squeeze(0),  # (T_motion,)
        }
    
    def _resample_feature(self, feature: np.ndarray, target_length: int) -> np.ndarray:
        """Resample feature array to target length using linear interpolation"""
        from scipy.interpolate import interp1d
        
        current_length = feature.shape[1]
        
        # Create interpolation function
        x_current = np.linspace(0, 1, current_length)
        x_target = np.linspace(0, 1, target_length)
        
        # Interpolate each feature dimension
        resampled = np.zeros((feature.shape[0], target_length))
        for i in range(feature.shape[0]):
            f = interp1d(x_current, feature[i, :], kind='linear')
            resampled[i, :] = f(x_target)
        
        return resampled
    
    def get_bpm(self, audio_path: str) -> float:
        """Quick BPM extraction without full feature extraction"""
        audio, sr = self.load_audio(audio_path)
        tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
        return float(tempo)


if __name__ == "__main__":
    # Test the processor
    import sys
    
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
    else:
        print("Usage: python audio_processor.py <audio_file>")
        print("Example: python audio_processor.py uploads/test.mp3")
        sys.exit(1)
    
    processor = AudioProcessor()
    features = processor.extract_features(audio_file)
    
    print("\n✅ Audio processing complete!")
    print(f"Total frames: {features['mel'].shape[1]}")
    print(f"Duration: {features['duration']:.2f}s")
