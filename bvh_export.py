"""
BVH (Biovision Hierarchy) File Exporter
Converts motion data to BVH format for animation software
"""

import numpy as np
from typing import List, Dict


class BVHExporter:
    """Export motion sequences to BVH file format"""
    
    #SMPL joint names (24 joints based on SMPL model)
    JOINT_NAMES = [
        "Pelvis",      # 0
        "L_Hip",       # 1
        "R_Hip",       # 2
        "Spine1",      # 3
        "L_Knee",      # 4
        "R_Knee",      # 5
        "Spine2",      # 6
        "L_Ankle",     # 7
        "R_Ankle",     # 8
        "Spine3",      # 9
        "L_Foot",      # 10
        "R_Foot",      # 11
        "Neck",        # 12
        "L_Collar",    # 13
        "R_Collar",    # 14
        "Head",        # 15
        "L_Shoulder",  # 16
        "R_Shoulder",  # 17
        "L_Elbow",     # 18
        "R_Elbow",     # 19
        "L_Wrist",     # 20
        "R_Wrist",     # 21
        "L_Hand",      # 22
        "R_Hand"       # 23
    ]
    
    # Parent indices for each joint (defines skeleton hierarchy)
    PARENT_INDICES = [
        -1,  # 0: Pelvis (root)
        0,   # 1: L_Hip -> Pelvis
        0,   # 2: R_Hip -> Pelvis
        0,   # 3: Spine1 -> Pelvis
        1,   # 4: L_Knee -> L_Hip
        2,   # 5: R_Knee -> R_Hip
        3,   # 6: Spine2 -> Spine1
        4,   # 7: L_Ankle -> L_Knee
        5,   # 8: R_Ankle -> R_Knee
        6,   # 9: Spine3 -> Spine2
        7,   # 10: L_Foot -> L_Ankle
        8,   # 11: R_Foot -> R_Ankle
        9,   # 12: Neck -> Spine3
        9,   # 13: L_Collar -> Spine3
        9,   # 14: R_Collar -> Spine3
        12,  # 15: Head -> Neck
        13,  # 16: L_Shoulder -> L_Collar
        14,  # 17: R_Shoulder -> R_Collar
        16,  # 18: L_Elbow -> L_Shoulder
        17,  # 19: R_Elbow -> R_Shoulder
        18,  # 20: L_Wrist -> L_Elbow
        19,  # 21: R_Wrist -> R_Elbow
        20,  # 22: L_Hand -> L_Wrist
        21   # 23: R_Hand -> R_Wrist
    ]
    
    def __init__(self, fps: int = 60):
        """
        Args:
            fps: Frames per second (default: 60)
        """
        self.fps = fps
        self.frame_time = 1.0 / fps
    
    def export(self, motion_data: np.ndarray, output_path: str, 
               translations: np.ndarray = None):
        """
        Export motion data to BVH file
        
        Args:
            motion_data: Joint rotations array (num_frames, num_joints, 3) - Euler angles in degrees
            output_path: Path to output BVH file
            translations: Root joint translations (num_frames, 3), optional
        """
        num_frames, num_joints, _ = motion_data.shape
        
        if num_joints != 24:
            print(f"⚠️  Warning: Expected 24 joints, got {num_joints}. Adjusting...")
        
        # Generate translations if not provided (static pose at origin)
        if translations is None:
            translations = np.zeros((num_frames, 3))
        
        print(f"\n📝 Exporting BVH file...")
        print(f"  - Frames: {num_frames}")
        print(f"  - FPS: {self.fps}")
        print(f"  - Duration: {num_frames / self.fps:.2f}s")
        
        with open(output_path, 'w') as f:
            # Write HIERARCHY section
            self._write_hierarchy(f)
            
            # Write MOTION section
            self._write_motion(f, motion_data, translations)
        
        print(f"✅ BVH exported to: {output_path}")
    
    def _write_hierarchy(self, file):
        """Write the HIERARCHY section of BVH file"""
        file.write("HIERARCHY\n")
        
        # Write each joint recursively
        self._write_joint(file, 0, 0)  # Start with root (Pelvis)
    
    def _write_joint(self, file, joint_idx: int, indent_level: int):
        """Recursively write joint hierarchy"""
        indent = "  " * indent_level
        joint_name = self.JOINT_NAMES[joint_idx]
        
        # Root joint uses "ROOT", others use "JOINT"
        if joint_idx == 0:
            file.write(f"{indent}ROOT {joint_name}\n")
        else:
            file.write(f"{indent}JOINT {joint_name}\n")
        
        file.write(f"{indent}{{\n")
        
        # Offset (bone length) - using approximate SMPL proportions
        offset = self._get_joint_offset(joint_idx)
        file.write(f"{indent}  OFFSET {offset[0]:.6f} {offset[1]:.6f} {offset[2]:.6f}\n")
        
        # Channels (degrees of freedom)
        if joint_idx == 0:
            # Root has 6 channels: position (XYZ) + rotation (ZXY)
            file.write(f"{indent}  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation\n")
        else:
            # Other joints have 3 rotation channels
            file.write(f"{indent}  CHANNELS 3 Zrotation Xrotation Yrotation\n")
        
        # Find and write children joints
        children = [i for i, parent in enumerate(self.PARENT_INDICES) if parent == joint_idx]
        
        if children:
            for child_idx in children:
                self._write_joint(file, child_idx, indent_level + 1)
        else:
            # End site for leaf joints
            file.write(f"{indent}  End Site\n")
            file.write(f"{indent}  {{\n")
            file.write(f"{indent}    OFFSET 0.0 0.0 0.0\n")
            file.write(f"{indent}  }}\n")
        
        file.write(f"{indent}}}\n")
    
    def _get_joint_offset(self, joint_idx: int) -> np.ndarray:
        """Get approximate bone offset for joint (in meters)"""
        # Approximate SMPL skeleton proportions (simplified)
        offsets = {
            0: [0.0, 0.0, 0.0],         # Pelvis (root)
            1: [0.1, -0.05, 0.0],       # L_Hip
            2: [-0.1, -0.05, 0.0],      # R_Hip
            3: [0.0, 0.1, 0.0],         # Spine1
            4: [0.0, -0.4, 0.0],        # L_Knee
            5: [0.0, -0.4, 0.0],        # R_Knee
            6: [0.0, 0.15, 0.0],        # Spine2
            7: [0.0, -0.4, 0.0],        # L_Ankle
            8: [0.0, -0.4, 0.0],        # R_Ankle
            9: [0.0, 0.15, 0.0],        # Spine3
            10: [0.0, -0.1, 0.1],       # L_Foot
            11: [0.0, -0.1, 0.1],       # R_Foot
            12: [0.0, 0.15, 0.0],       # Neck
            13: [0.15, 0.05, 0.0],      # L_Collar
            14: [-0.15, 0.05, 0.0],     # R_Collar
            15: [0.0, 0.15, 0.0],       # Head
            16: [0.2, 0.0, 0.0],        # L_Shoulder
            17: [-0.2, 0.0, 0.0],       # R_Shoulder
            18: [0.25, 0.0, 0.0],       # L_Elbow
            19: [-0.25, 0.0, 0.0],      # R_Elbow
            20: [0.25, 0.0, 0.0],       # L_Wrist
            21: [-0.25, 0.0, 0.0],      # R_Wrist
            22: [0.1, 0.0, 0.0],        # L_Hand
            23: [-0.1, 0.0, 0.0],       # R_Hand
        }
        
        return np.array(offsets.get(joint_idx, [0.0, 0.0, 0.0]))
    
    def _write_motion(self, file, motion_data: np.ndarray, translations: np.ndarray):
        """Write the MOTION section of BVH file"""
        num_frames = motion_data.shape[0]
        
        file.write("MOTION\n")
        file.write(f"Frames: {num_frames}\n")
        file.write(f"Frame Time: {self.frame_time:.6f}\n")
        
        # Write each frame
        for frame_idx in range(num_frames):
            frame_data = []
            
            # Root translation (frame 0)
            frame_data.extend(translations[frame_idx].tolist())
            
            # Root rotation and all joint rotations
            for joint_idx in range(motion_data.shape[1]):
                # Euler angles in ZXY order (standard BVH)
                rotation = motion_data[frame_idx, joint_idx, :]
                frame_data.extend(rotation.tolist())
            
            # Write frame line
            frame_str = " ".join([f"{val:.6f}" for val in frame_data])
            file.write(f"{frame_str}\n")


if __name__ == "__main__":
    # Test BVH export with dummy data
    print("Testing BVH exporter...")
    
    # Create dummy motion data (simple T-pose with small arm movement)
    num_frames = 60
    num_joints = 24
    
    motion = np.zeros((num_frames, num_joints, 3))
    
    # Add some simple arm motion
    for i in range(num_frames):
        angle = (i / num_frames) * 90  # 0 to 90 degrees
        motion[i, 16, 2] = angle  # L_Shoulder Z rotation
        motion[i, 17, 2] = -angle  # R_Shoulder Z rotation
    
    # Create dummy translations (stationary)
    translations = np.zeros((num_frames, 3))
    translations[:, 1] = 1.0  # 1 meter above ground
    
    # Export
    exporter = BVHExporter(fps=60)
    exporter.export(motion, "test_output.bvh", translations)
