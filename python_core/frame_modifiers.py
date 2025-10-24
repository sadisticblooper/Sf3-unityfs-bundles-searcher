import numpy as np
import struct
from io import BytesIO

def process_bone_data(bone_data, modifier=None):
    """
    Reads 12 bytes of bone data (6 pos, 6 rot), applies a modifier function 
    to position data (3 values), and returns the new 12 bytes.
    This function is CRITICAL for binary integrity (normalization/re-packing of float16).
    """
    
    if len(bone_data) < 12:
        return None
    
    position_bytes = bone_data[:6]
    rotation_bytes = bone_data[6:]
    
    # Process and Clean Position Data
    pos_np = np.frombuffer(position_bytes, dtype=np.float16, count=3).astype(float)
    
    if modifier:
        pos_np = modifier(pos_np)
        
    new_position_bytes = np.array(pos_np, dtype=np.float16).tobytes()
    
    # Process and Clean Rotation Data
    rot_np = np.frombuffer(rotation_bytes, dtype=np.float16, count=3).astype(float)
    new_rotation_bytes = np.array(rot_np, dtype=np.float16).tobytes()
    
    return new_position_bytes + new_rotation_bytes


def shorten_animation_data(data_stream, frames_length, bone_ids, output_stream, factor_n, factor_d):
    """
    Shortens animation data using rational decimation based on factor_n/factor_d.
    """
    success = True
    new_frames_length = 0
    
    if factor_n <= 0 or factor_d <= 0:
        print(f"Error: Invalid shorten factors A_prime={factor_n}, B_prime={factor_d}.")
        return frames_length, False 
    
    bone_count = len(bone_ids)
    frame_size_bytes = bone_count * 12
    frame_data_block_bytes = data_stream.read(frames_length * frame_size_bytes)
    
    if len(frame_data_block_bytes) != frames_length * frame_size_bytes:
        print(f"Warning: Expected {frames_length * frame_size_bytes} frame bytes, but read only {len(frame_data_block_bytes)}. File may be malformed.")

    frame_block_stream = BytesIO(frame_data_block_bytes)

    for frame_id in range(frames_length):
        keep_frame = ((frame_id % factor_n) < factor_d)
        
        for _ in range(bone_count):
            bone_data = frame_block_stream.read(12)
            
            if len(bone_data) < 12:
                print(f"Error: Unexpected end of bone data in frame {frame_id}.")
                success = False
                break
                
            if keep_frame:
                modified_data = process_bone_data(bone_data) 
                if modified_data:
                    output_stream.write(modified_data)
        
        if not success:
            break
            
        if keep_frame:
            new_frames_length += 1

    return new_frames_length, success


def lengthen_animation_data(data_stream, frames_length, bone_ids, output_stream, factor_n, factor_d=1):
    """
    Lengthens animation data by simple frame duplication. No interpolation.
    This guarantees accurate frame counts and eliminates jitter.
    """
    factor = int(factor_n)
    if factor < 1:
        factor = 1

    success = True
    new_frames_length = 0
    bone_count = len(bone_ids)
    frame_size_bytes = bone_count * 12
    
    # Read the entire animation data block into memory to prevent read errors.
    animation_data_bytes = data_stream.read(frames_length * frame_size_bytes)
    
    if len(animation_data_bytes) != frames_length * frame_size_bytes:
        print(f"Warning: Expected {frames_length * frame_size_bytes} frame bytes, but read only {len(animation_data_bytes)}. File may be malformed.")

    # Iterate through each original frame from the in-memory block.
    for frame_id in range(frames_length):
        frame_offset = frame_id * frame_size_bytes
        raw_frame_data = animation_data_bytes[frame_offset : frame_offset + frame_size_bytes]

        if len(raw_frame_data) < frame_size_bytes:
            print(f"Error: Not enough data for frame {frame_id}. Stopping.")
            success = False
            break

        # Clean the frame data once before duplicating it.
        cleaned_frame_data = b''
        for bone_idx in range(bone_count):
            bone_offset = bone_idx * 12
            raw_bone_data = raw_frame_data[bone_offset : bone_offset + 12]
            processed_data = process_bone_data(raw_bone_data)
            if not processed_data:
                print(f"Error: Bone data processing failed for frame {frame_id}, bone {bone_idx}.")
                success = False
                break
            cleaned_frame_data += processed_data
        
        if not success:
            break
            
        # Write the cleaned frame data 'factor' times.
        for _ in range(factor):
            output_stream.write(cleaned_frame_data)
            new_frames_length += 1
            
    # The final frame count should be exact.
    expected_frames = frames_length * factor
    if new_frames_length != expected_frames:
        print(f"Warning: Frame count mismatch. Expected {expected_frames}, but got {new_frames_length}.")

    return new_frames_length, success


def x_double_animation_data(data_stream, frames_length, bone_ids, output_stream, factor_n=1, factor_d=1):
    """Doubles the X position of every bone in every frame."""
    success = True
    
    def modifier(pos_np):
        pos_np[0] *= 2.0
        return pos_np

    bone_count = len(bone_ids)
    frame_size_bytes = bone_count * 12

    frame_data_block_bytes = data_stream.read(frames_length * frame_size_bytes)
    frame_block_stream = BytesIO(frame_data_block_bytes)

    for frame_id in range(frames_length):
        for _ in range(bone_count):
            bone_data = frame_block_stream.read(12)
            
            if len(bone_data) < 12:
                print(f"Error: Unexpected end of bone data in frame {frame_id}.")
                success = False
                break
            
            modified_data = process_bone_data(bone_data, modifier)
            if modified_data:
                output_stream.write(modified_data)

        if not success:
            break
            
    new_frames_length = frames_length 
    return new_frames_length, success


def dash_animation_data(data_stream, frames_length, bone_ids, output_stream, offset_factor, direction_sign=1):
    """
    Applies a progressive X offset (Dash) only to the PELVIS (Bone ID 0).
    """
    success = True
    bone_count = len(bone_ids)
    frame_size_bytes = bone_count * 12

    frame_data_block_bytes = data_stream.read(frames_length * frame_size_bytes)
    frame_block_stream = BytesIO(frame_data_block_bytes)
    max_frame_index = frames_length - 1

    for frame_id in range(frames_length):
        current_offset = (max_frame_index - frame_id) * offset_factor * direction_sign
        
        def pelvis_modifier(pos_np, offset=current_offset):
            pos_np[0] += offset
            return pos_np
            
        def no_op_modifier(pos_np):
            return pos_np

        for bone_index in range(bone_count):
            bone_data = frame_block_stream.read(12)
            
            if len(bone_data) < 12:
                print(f"Error: Unexpected end of bone data in frame {frame_id}.")
                success = False
                break
            
            current_bone_id = bone_ids[bone_index] 
            
            modifier_to_use = pelvis_modifier if current_bone_id == 0 else no_op_modifier
            
            modified_data = process_bone_data(bone_data, modifier_to_use)
            if modified_data:
                output_stream.write(modified_data)
            else:
                success = False
                break

        if not success:
            break
            
    new_frames_length = frames_length 
    return new_frames_length, success


def split_dash_animation_data(data_stream, frames_length, bone_ids, output_stream, order, phase1_frames, phase1_offset_factor, phase2_offset_factor):
    """
    Applies a two-part progressive X offset with a smooth transition.
    """
    success = True
    bone_count = len(bone_ids)
    frame_size_bytes = bone_count * 12

    frame_data_block_bytes = data_stream.read(frames_length * frame_size_bytes)
    
    raw_offsets = np.zeros(frames_length, dtype=float)
    
    phase1_dir = +1 if order == 'towards_first' else -1
    phase2_dir = -1 if order == 'towards_first' else +1

    phase1_len = phase1_frames
    if phase1_len > 0:
        max_p1_idx = phase1_len - 1
        for i in range(phase1_len):
            raw_offsets[i] = (max_p1_idx - i) * phase1_offset_factor * phase1_dir
    
    phase2_start = phase1_frames
    phase2_len = frames_length - phase2_start
    if phase2_len > 0:
        max_p2_idx = phase2_len - 1
        for i in range(phase2_len):
            frame_id = phase2_start + i
            raw_offsets[frame_id] = (max_p2_idx - i) * phase2_offset_factor * phase2_dir

    breakpoint_frame = phase1_frames
    transition_start = max(0, breakpoint_frame - 5)
    transition_end = min(frames_length - 1, breakpoint_frame + 4)
    transition_len = transition_end - transition_start + 1

    if transition_len > 1:
        start_offset = raw_offsets[transition_start]
        end_offset = raw_offsets[transition_end]
        
        for i in range(transition_len):
            frame_index = transition_start + i
            t = i / (transition_len - 1)
            smoothed_offset = (1 - t) * start_offset + t * end_offset
            raw_offsets[frame_index] = smoothed_offset

    frame_block_stream = BytesIO(frame_data_block_bytes)

    for frame_id in range(frames_length):
        final_offset_for_frame = raw_offsets[frame_id]
        
        def pelvis_modifier(pos_np, offset=final_offset_for_frame):
            pos_np[0] += offset
            return pos_np
            
        def no_op_modifier(pos_np):
            return pos_np

        for bone_index in range(bone_count):
            bone_data = frame_block_stream.read(12)
            
            if len(bone_data) < 12:
                print(f"Error: Unexpected end of bone data in frame {frame_id}.")
                success = False
                break
            
            current_bone_id = bone_ids[bone_index] 
            
            modifier_to_use = pelvis_modifier if current_bone_id == 0 else no_op_modifier
            
            modified_data = process_bone_data(bone_data, modifier_to_use)
            if modified_data:
                output_stream.write(modified_data)
            else:
                success = False
                break

        if not success:
            break
            
    new_frames_length = frames_length 
    return new_frames_length, success


def birth_location_animation_data(data_stream, frames_length, bone_ids, output_stream, total_offset, direction_sign, initial_x):
    """
    Applies a smooth, linearly increasing X offset to the PELVIS (Bone ID 0).
    """
    success = True
    bone_count = len(bone_ids)
    frame_size_bytes = bone_count * 12

    frame_data_block_bytes = data_stream.read(frames_length * frame_size_bytes)
    frame_block_stream = BytesIO(frame_data_block_bytes)
    RAMP_UP_DURATION = 30
    effective_ramp_frames = min(RAMP_UP_DURATION, frames_length)
    
    if effective_ramp_frames <= 1:
        lerp_divisor = 1.0 
    else:
        lerp_divisor = float(effective_ramp_frames - 1)

    final_signed_offset = total_offset * direction_sign

    for frame_id in range(frames_length):
        
        current_offset = 0.0
        if frame_id < effective_ramp_frames:
            t = frame_id / lerp_divisor 
            current_offset = final_signed_offset * t
        else:
            current_offset = final_signed_offset
        
        def pelvis_modifier(pos_np, offset=current_offset, start_x=initial_x):
            pos_np[0] = start_x + offset
            return pos_np
            
        def no_op_modifier(pos_np):
            return pos_np

        for bone_index in range(bone_count):
            bone_data = frame_block_stream.read(12)
            
            if len(bone_data) < 12:
                print(f"Error: Unexpected end of bone data in frame {frame_id}.")
                success = False
                break
            
            current_bone_id = bone_ids[bone_index] 
            modifier_to_use = pelvis_modifier if current_bone_id == 0 else no_op_modifier
            
            modified_data = process_bone_data(bone_data, modifier_to_use)
            if modified_data:
                output_stream.write(modified_data)
            else:
                success = False
                break

        if not success:
            break
            
    new_frames_length = frames_length 
    return new_frames_length, success


def trimmer_animation_data(data_stream, frames_length, bone_ids, output_stream, start_frame, end_frame):
    """
    Removes specific frame ranges from animation.
    """
    success = True
    new_frames_length = 0
    bone_count = len(bone_ids)
    frame_size_bytes = bone_count * 12

    frame_data_block_bytes = data_stream.read(frames_length * frame_size_bytes)
    
    if len(frame_data_block_bytes) != frames_length * frame_size_bytes:
        print(f"Warning: Expected {frames_length * frame_size_bytes} frame bytes, but read only {len(frame_data_block_bytes)}. File may be malformed.")

    frame_block_stream = BytesIO(frame_data_block_bytes)

    for frame_id in range(frames_length):
        if start_frame <= frame_id <= end_frame:
            frame_block_stream.read(frame_size_bytes)
            continue
        
        frame_data = frame_block_stream.read(frame_size_bytes)
        if len(frame_data) < frame_size_bytes:
            print(f"Error: Unexpected end of file at frame {frame_id}.")
            success = False
            break

        frame_bone_stream = BytesIO(frame_data)
        cleaned_frame_data = b''
        
        for _ in range(bone_count):
            bone_data_raw = frame_bone_stream.read(12)
            processed_data = process_bone_data(bone_data_raw)
            if not processed_data:
                print(f"Error: Bone data processing failed in TRIMMER for frame {frame_id}.")
                success = False
                break
            cleaned_frame_data += processed_data
        
        if not success:
            break
            
        output_stream.write(cleaned_frame_data)
        new_frames_length += 1

    return new_frames_length, success


def axis_adder_animation_data(data_stream, frames_length, bone_ids, output_stream, x_offset=0.0, y_offset=0.0, z_offset=0.0, bone_id=-1):
    """
    Adds constant values to X, Y, Z axes for specific bones.
    """
    success = True
    bone_count = len(bone_ids)
    frame_size_bytes = bone_count * 12

    frame_data_block_bytes = data_stream.read(frames_length * frame_size_bytes)
    frame_block_stream = BytesIO(frame_data_block_bytes)

    for frame_id in range(frames_length):
        for bone_index in range(bone_count):
            bone_data = frame_block_stream.read(12)
            
            if len(bone_data) < 12:
                print(f"Error: Unexpected end of bone data in frame {frame_id}.")
                success = False
                break
            
            current_bone_id = bone_ids[bone_index]
            
            if bone_id == -1 or current_bone_id == bone_id:
                def axis_adder_modifier(pos_np, x_off=x_offset, y_off=y_offset, z_off=z_offset):
                    pos_np[0] += x_off
                    pos_np[1] += y_off
                    pos_np[2] += z_off
                    return pos_np
                modifier_to_use = axis_adder_modifier
            else:
                modifier_to_use = None
            
            modified_data = process_bone_data(bone_data, modifier_to_use)
            if modified_data:
                output_stream.write(modified_data)
            else:
                success = False
                break

        if not success:
            break
            
    new_frames_length = frames_length 
    return new_frames_length, success


def axis_scaler_animation_data(data_stream, frames_length, bone_ids, output_stream, scale_factor, target_bone_ids):
    """
    Scales the position coordinates (X, Y, Z) for specific bones by a scale factor,
    with progressive scaling over the first 10 frames for smooth transition.
    
    Args:
        data_stream: Input stream containing animation data
        frames_length: Number of frames in the animation
        bone_ids: List of bone IDs in the animation
        output_stream: Output stream for modified data
        scale_factor: Final factor to multiply position coordinates by
        target_bone_ids: List of bone IDs to apply scaling to
    """
    success = True
    bone_count = len(bone_ids)
    frame_size_bytes = bone_count * 12

    frame_data_block_bytes = data_stream.read(frames_length * frame_size_bytes)
    frame_block_stream = BytesIO(frame_data_block_bytes)
    
    # Progressive scaling over first 10 frames
    PROGRESSIVE_FRAMES = 10
    progressive_frames = min(PROGRESSIVE_FRAMES, frames_length)
    
    # Calculate progressive scale factors for each frame
    progressive_factors = []
    if progressive_frames > 1:
        # Start from 1.0 and gradually approach the target scale_factor
        for frame_idx in range(frames_length):
            if frame_idx < progressive_frames:
                # Linear progression from 1.0 to scale_factor
                t = frame_idx / (progressive_frames - 1)
                current_factor = 1.0 + (scale_factor - 1.0) * t
                progressive_factors.append(current_factor)
            else:
                # After progressive frames, use the final scale factor
                progressive_factors.append(scale_factor)
    else:
        # If only 1 frame or less, just use the final scale factor
        progressive_factors = [scale_factor] * frames_length

    for frame_id in range(frames_length):
        current_scale_factor = progressive_factors[frame_id]
        
        for bone_index in range(bone_count):
            bone_data = frame_block_stream.read(12)
            
            if len(bone_data) < 12:
                print(f"Error: Unexpected end of bone data in frame {frame_id}.")
                success = False
                break
            
            current_bone_id = bone_ids[bone_index]
            
            # Apply scaling only to target bones (empty target_bone_ids means all bones)
            if not target_bone_ids or current_bone_id in target_bone_ids:
                def scaler_modifier(pos_np, scale=current_scale_factor):
                    pos_np[0] *= scale
                    pos_np[1] *= scale
                    pos_np[2] *= scale
                    return pos_np
                modifier_to_use = scaler_modifier
            else:
                modifier_to_use = None
            
            modified_data = process_bone_data(bone_data, modifier_to_use)
            if modified_data:
                output_stream.write(modified_data)
            else:
                success = False
                break

        if not success:
            break
            
    new_frames_length = frames_length 
    return new_frames_length, success