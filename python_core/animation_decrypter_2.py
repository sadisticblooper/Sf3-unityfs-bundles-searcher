import struct
import sys
import os
from io import BytesIO
import csv
import math
import warnings
import glob 
import re 

try:
    import numpy as np
except ImportError:
    # The logger won't exist in a pure CLI context, so fallback to print
    print("Error: This script requires the 'numpy' library.")
    print("Please install it: pip install numpy")
    sys.exit(1)

from frame_modifiers import (
    shorten_animation_data, lengthen_animation_data, x_double_animation_data, 
    dash_animation_data, birth_location_animation_data, process_bone_data,
    split_dash_animation_data, trimmer_animation_data, axis_adder_animation_data,
    axis_scaler_animation_data  # NEW
)

# --- Configuration ---
PROMPT_TO_DELETE_FILES = True 
# UPDATED: Added AXIS_SCALER_ prefix regex
PREFIX_REGEXES = [
    r'^LENGTHEN_x\d+_', r'^SHORTEN_x\d+[_]\d+_', r'^SHORTEN_x\d+_', r'^X_DOUBLE_',
    r'^DASH_[PN]_x[\d_]+_', r'^SPLIT_DASH_[TA]_FIRST_T\d+_A\d+_x[\d_]+_x[\d_]+_',
    r'^BIRTH_LOC_[PN]_x[\d_]+_', r'^SPLICER_[\d_]+_', r'^REPACKED_', r'^EXTRACTED_', 
    r'^TRIMMER_', r'^AXIS_ADDER_', r'^AXIS_SCALER_'  # NEW
]
# UPDATED: Added _AXIS_SCALED suffix regex
SUFFIX_REGEXES = [
    r'_ORIGINAL$', r'_EXTRACTED$', r'_REPACKED$', r'_X_DOUBLE$', r'_DASH_[PN]_x[\d_]+$',
    r'_SPLIT_DASH_[TA]_FIRST_T\d+_A\d+_x[\d_]+_x[\d_]+$', r'_BIRTH_LOC_[PN]_x[\d_]+$',
    r'_SHORTENED_x\d+[_]\d+$', r'_SHORTENED_x\d+$', r'_LENGTHENED_x\d+$',
    r'_SPLICER_[\d_]+$', r'_TRIMMED$', r'_AXIS_ADDED$', r'_AXIS_SCALED$'  # NEW
]
OPERATION_MODE = {
    '1': ('SHORTEN', "Shortens animation by a factor."),
    '2': ('LENGTHEN', "Lengthens animation by a factor."),
    '3': ('EXTRACT_CSV', "Extracts animation data to a CSV file."),
    '4': ('SPLICER', "Splices two animations with matching bone structures."),
    '5': ('DASH', "Applies a dash effect."),
    '6': ('BIRTH_LOCATION', "Applies a birth location offset."),
    '7': ('X_DOUBLE', "Doubles the X-axis values."),
    '8': ('TRIMMER', "Removes a range of frames."),
    '9': ('AXIS_ADDER', "Adds a value to a specific axis."),
    '10': ('AXIS_SCALER', "Scales position coordinates for selected bones."),  # NEW
}
BONE_MAP = {
    0: "pelvis", 1: "stomach", 2: "chest", 3: "neck", 4: "head", 5: "hair", 6: "hair1",
    7: "zero_joint_hand_l", 8: "clavicle_l", 9: "arm_l", 10: "forearm_l",
    11: "forearm_twist_l", 12: "hand_l", 13: "weapon_l", 14: "f_big1_l", 15: "f_big2_l", 16: "f_big3_l",
    17: "f_main1_l", 18: "f_main2_l", 19: "f_main3_l", 20: "f_pointer1_l", 21: "f_pointer2_l", 22: "f_pointer3_l",
    23: "scapular_l", 24: "chest_l", 25: "zero_joint_hand_r", 26: "clavicle_r", 27: "arm_r", 28: "forearm_r",
    29: "forearm_twist_r", 30: "hand_r", 31: "weapons_r", 32: "f_big1_r", 33: "f_big2_r", 34: "f_big3_r",
    35: "f_main1_r", 36: "f_main2_r", 37: "f_main3_r", 38: "f_pointer1_r", 39: "f_pointer2_r", 40: "f_pointer3_r",
    41: "scapular_r", 42: "chest_r", 43: "zero_joint_pelvis_l", 44: "thigh_l", 45: "calf_l", 46: "foot_l",
    47: "toe_l", 48: "back_l", 49: "chest_h_49", 50: "stomach_h_50",
    51: "zero_joint_pelvis_r", 52: "thigh_r", 53: "calf_r", 54: "foot_r", 55: "toe_r", 56: "back_r",
    57: "biceps_twist_l", 58: "biceps_twist_r", 59: "thigh_twist_l", 60: "thigh_twist_r",
    61: "foot_r_extra", 62: "toe_r_extra", 63: "weapon_r_extra", 64: "weapon_l_extra", 65: "root_extra",
}
EXPECTED_HEADER = 457546134634734

# --- Utility functions ---

def get_bone_name(bone_id):
    return BONE_MAP.get(bone_id, f"Unknown_Bone_{bone_id}")

def parse_header_metadata(data_stream):
    header_bytes = data_stream.read(8)
    if len(header_bytes) < 8: return None
    header = struct.unpack('<Q', header_bytes)[0]
    if header != EXPECTED_HEADER: return None
    
    garbage_size_bytes = data_stream.read(2)
    if not garbage_size_bytes: return None
    garbage_size = struct.unpack('<h', garbage_size_bytes)[0]
    garbage_data_size_in_bytes = garbage_size * 8
    garbage_data = data_stream.read(garbage_data_size_in_bytes)
    if len(garbage_data) < garbage_data_size_in_bytes: return None

    frames_length_bytes = data_stream.read(4)
    bone_ids_length_bytes = data_stream.read(4)
    if not frames_length_bytes or not bone_ids_length_bytes: return None
    frames_length = struct.unpack('<i', frames_length_bytes)[0]
    bone_ids_length = struct.unpack('<i', bone_ids_length_bytes)[0]

    bone_ids_bytes = data_stream.read(bone_ids_length * 2)
    if len(bone_ids_bytes) < bone_ids_length * 2: return None
    bone_ids = struct.unpack(f'<{bone_ids_length}h', bone_ids_bytes)
    
    static_header_block = (
        header_bytes + garbage_size_bytes + garbage_data + 
        frames_length_bytes + bone_ids_length_bytes + bone_ids_bytes
    )
    
    return {
        'static_header_block': static_header_block, 'frames_length': frames_length,
        'bone_ids': bone_ids, 'data_stream_position': data_stream.tell(),
        'garbage_data_size': garbage_data_size_in_bytes
    }

def generate_output_filename(original_filepath, operation_tag, is_binary_output=True, export_extension='.bytes'):
    file_name = os.path.basename(original_filepath)
    base_name, _ = os.path.splitext(file_name)
    
    for pattern in PREFIX_REGEXES:
        base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE)
    for pattern in SUFFIX_REGEXES:
        base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE)

    final_extension = export_extension if is_binary_output else '.csv'
    new_name = f"{operation_tag}_{base_name}{final_extension}"
    
    return os.path.join(os.path.dirname(original_filepath), new_name)

def get_decimation_params(float_factor, logger=print):
    if float_factor < 1.0:
        warnings.warn("Shorten factor must be 1.0 or greater. Using 1.0.")
        float_factor = 1.0
        
    inverse_ratio = 1.0 / float_factor
    numerator_inv = int(round(inverse_ratio * 10))
    denominator_inv = 10

    common_inv = math.gcd(numerator_inv, denominator_inv)
    factor_d = numerator_inv // common_inv
    factor_n = denominator_inv // common_inv

    logger(f"   Decimation ratio: {float_factor} -> Keep {factor_d} frames out of every {factor_n} input frames.")
    return factor_n, factor_d

def check_pelvis_x_static(data_stream, frames_length, bone_ids):
    if frames_length == 0: 
        return True, 0.0

    try:
        pelvis_index = bone_ids.index(0)
    except ValueError:
        return True, 0.0
    
    current_pos = data_stream.tell()
    data_stream.seek(current_pos + pelvis_index * 12)
    bone_data = data_stream.read(12)
    data_stream.seek(current_pos)
    
    if len(bone_data) < 12: 
        return True, 0.0

    pos_np = np.frombuffer(bone_data[:6], dtype=np.float16, count=3).astype(float)
    initial_x = pos_np[0]
    
    return True, initial_x

def modify_and_repack_animation_data(file_path, original_data, operation, factor_n, factor_d, logger=print, initial_x=None, **kwargs):
    logger(f"\n--- Starting Data Processing for: {os.path.basename(file_path)} ---")
    
    if operation == 'SHORTEN':
        factor_str = f"Keep {factor_d}/{factor_n}"
    elif operation == 'DASH':
        direction_str = "Towards" if factor_d == 1 else "Away"
        factor_str = f"Offset: {factor_n} ({direction_str})"
    elif operation == 'SPLIT_DASH':
        order = 'Towards first' if kwargs.get('order') == 'towards_first' else 'Away first'
        p1f = kwargs.get('phase1_frames', 0)
        p1o = kwargs.get('phase1_offset', 0)
        p2o = kwargs.get('phase2_offset', 0)
        factor_str = f"Order: {order}, P1 Frames: {p1f}, P1 Offset: {p1o}, P2 Offset: {p2o}"
    elif operation == 'BIRTH_LOCATION':
        direction_str = "Towards" if factor_d == 1 else "Away"
        factor_str = f"Total Offset: {factor_n} ({direction_str})"
    elif operation == 'TRIMMER':
        range_str = kwargs.get('range', '0-0')
        start, end = map(int, range_str.split('-'))
        factor_str = f"Remove frames: {start+1} to {end+1}"
    elif operation == 'AXIS_ADDER':
        x_offset = kwargs.get('x_offset', 0.0)
        y_offset = kwargs.get('y_offset', 0.0)
        z_offset = kwargs.get('z_offset', 0.0)
        bone_id = kwargs.get('bone_id', -1)
        factor_str = f"Offsets: X={x_offset}, Y={y_offset}, Z={z_offset}, Bone={bone_id}"
    elif operation == 'AXIS_SCALER':  # NEW
        scale_factor = kwargs.get('scale_factor', 1.0)
        target_bone_ids = kwargs.get('target_bone_ids', [])
        bone_count_str = f"{len(target_bone_ids)} bones" if target_bone_ids else "all bones"
        factor_str = f"Scale: {scale_factor} for {bone_count_str}"
    else:
        factor_str = str(factor_n)
        
    logger(f"--- Operation: {operation} (Factor: {factor_str}) ---")
    
    data_stream = BytesIO(original_data)
    
    metadata = parse_header_metadata(data_stream)
    if not metadata: 
        logger(f"Error: Invalid file header or metadata structure.")
        return False, None, None
    
    if operation == 'BIRTH_LOCATION' and initial_x is None:
        data_stream_temp = BytesIO(original_data)
        metadata_temp = parse_header_metadata(data_stream_temp)
        data_stream_temp.seek(metadata_temp['data_stream_position'])
        _, initial_x = check_pelvis_x_static(data_stream_temp, metadata_temp['frames_length'], metadata_temp['bone_ids'])
        if initial_x is None:
             logger(f"Error: Internal error. Could not establish static X coordinate for BIRTH_LOCATION.")
             return False, None, None

    bone_count = len(metadata['bone_ids'])
    logger(f"   Original frames: {metadata['frames_length']}, Animated bones: {bone_count}. Modifying...")

    data_stream.seek(metadata['data_stream_position'])
    
    modified_frame_data_stream = BytesIO()
    
    op_func = {
        'SHORTEN': shorten_animation_data, 'LENGTHEN': lengthen_animation_data,
        'X_DOUBLE': x_double_animation_data, 'DASH': dash_animation_data, 
        'BIRTH_LOCATION': birth_location_animation_data, 'SPLIT_DASH': split_dash_animation_data,
        'TRIMMER': trimmer_animation_data, 'AXIS_ADDER': axis_adder_animation_data,
        'AXIS_SCALER': axis_scaler_animation_data  # NEW
    }.get(operation)

    tag = operation
    if op_func:
        if operation == 'DASH':
            new_frames_length, success_op = op_func(data_stream, metadata['frames_length'], metadata['bone_ids'], modified_frame_data_stream, offset_factor=factor_n, direction_sign=factor_d)
            direction_char = 'P' if factor_d == 1 else 'N'
            tag = f"DASH_{direction_char}_x{str(factor_n).replace('.', '_')}"
        elif operation == 'SPLIT_DASH':
            order, p1f, p1o, p2o = [kwargs.get(k) for k in ['order', 'phase1_frames', 'phase1_offset', 'phase2_offset']]
            new_frames_length, success_op = op_func(
                data_stream, metadata['frames_length'], metadata['bone_ids'], modified_frame_data_stream, 
                order=order, phase1_frames=p1f, phase1_offset_factor=p1o, phase2_offset_factor=p2o
            )
            order_char = 'T' if order == 'towards_first' else 'A'
            tag = f"SPLIT_DASH_{order_char}_FIRST"
        elif operation == 'BIRTH_LOCATION':
            new_frames_length, success_op = op_func(
                data_stream, metadata['frames_length'], metadata['bone_ids'], modified_frame_data_stream, 
                total_offset=factor_n, direction_sign=factor_d, initial_x=initial_x
            )
            direction_char = 'P' if factor_d == 1 else 'N'
            tag = f"BIRTH_LOC_{direction_char}_x{str(factor_n).replace('.', '_')}"
        elif operation == 'SHORTEN':
            new_frames_length, success_op = op_func(data_stream, metadata['frames_length'], metadata['bone_ids'], modified_frame_data_stream, factor_n, factor_d)
            tag = f"SHORTEN_x{kwargs.get('float_factor_str')}"
        elif operation == 'LENGTHEN':
            new_frames_length, success_op = op_func(data_stream, metadata['frames_length'], metadata['bone_ids'], modified_frame_data_stream, factor_n, factor_d)
            tag = f"LENGTHEN_x{factor_n}"
        elif operation == 'TRIMMER':
            range_str = kwargs.get('range', '0-0')
            start_frame, end_frame = map(int, range_str.split('-'))
            new_frames_length, success_op = op_func(data_stream, metadata['frames_length'], metadata['bone_ids'], modified_frame_data_stream, start_frame, end_frame)
            tag = "TRIMMER"
        elif operation == 'AXIS_ADDER':
            x_offset, y_offset, z_offset, bone_id = [kwargs.get(k) for k in ['x_offset', 'y_offset', 'z_offset', 'bone_id']]
            new_frames_length, success_op = op_func(
                data_stream, metadata['frames_length'], metadata['bone_ids'], modified_frame_data_stream,
                x_offset=float(x_offset), y_offset=float(y_offset), z_offset=float(z_offset), bone_id=int(bone_id)
            )
            tag = "AXIS_ADDER"
        elif operation == 'AXIS_SCALER':  # NEW
            scale_factor = float(kwargs.get('scale_factor', 1.0))
            target_bone_ids = kwargs.get('target_bone_ids', [])
            new_frames_length, success_op = op_func(
                data_stream, metadata['frames_length'], metadata['bone_ids'], modified_frame_data_stream,
                scale_factor=scale_factor, target_bone_ids=target_bone_ids
            )
            bone_count_str = f"{len(target_bone_ids)}bones" if target_bone_ids else "allbones"
            tag = f"AXIS_SCALER_x{str(scale_factor).replace('.', '_')}_{bone_count_str}"
        else: # X_DOUBLE
            new_frames_length, success_op = op_func(data_stream, metadata['frames_length'], metadata['bone_ids'], modified_frame_data_stream, factor_n, factor_d)
            tag = "X_DOUBLE"
    else:
        logger(f"Error: Internal error. Unknown operation mode '{operation}'.")
        return False, None, None
        
    if not success_op:
        logger(f"Error: Operation '{operation}' failed during execution.")
        return False, None, None
        
    logger(f"   New frame count: {new_frames_length}")

    modified_frame_data = modified_frame_data_stream.getvalue()
    
    expected_data_size = new_frames_length * bone_count * 12
    actual_data_size = len(modified_frame_data)
    
    if actual_data_size != expected_data_size:
        logger(f"CRITICAL ERROR: Data size mismatch after modification (Op: {operation}).")
        logger(f"Expected: {expected_data_size} bytes. Actual: {actual_data_size} bytes.")
        return False, None, None

    original_remaining_data = data_stream.read()
    remaining_data = original_remaining_data 
    
    if operation == 'LENGTHEN':
        factor = int(round(factor_n))
        if factor > 1 and len(original_remaining_data) > 0:
            logger(f"   Duplicating {len(original_remaining_data)} bytes of tail data {factor} times.")
            remaining_data = original_remaining_data * factor
            logger(f"   New tail data size: {len(remaining_data)} bytes.")
        elif len(original_remaining_data) > 0:
            logger(f"Warning: Found {len(original_remaining_data)} bytes of unparsed tail data. Appending them.")
    elif len(original_remaining_data) > 0:
        logger(f"Warning: Found {len(original_remaining_data)} bytes of unparsed tail data. Appending them.")
    
    final_modified_bytes = reconstruct_binary(metadata, new_frames_length, modified_frame_data, remaining_data)
    
    return True, final_modified_bytes, tag

def reconstruct_binary(metadata, new_frames_length, modified_frame_data, remaining_data):
    garbage_size_in_bytes = metadata.get('garbage_data_size', 0)
    frames_length_position = 8 + 2 + garbage_size_in_bytes
    
    header_part1 = metadata['static_header_block'][:frames_length_position]
    header_part2 = metadata['static_header_block'][frames_length_position + 4:]
    
    new_frames_length_bytes = struct.pack('<i', new_frames_length)
    modified_header_block = header_part1 + new_frames_length_bytes + header_part2
    
    return modified_header_block + modified_frame_data + remaining_data

def extract_data_and_metadata(binary_data_stream):
    binary_data_stream.seek(0)
    metadata = parse_header_metadata(binary_data_stream)
    if not metadata: return None, None
    
    csv_metadata_row = ["METADATA_HEADER", metadata['static_header_block'].hex()]
    csv_rows = []

    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=RuntimeWarning)
        for frame_id in range(metadata['frames_length']):
            for bone_id_int in metadata['bone_ids']:
                bone_data = binary_data_stream.read(12)
                if len(bone_data) < 12: return csv_metadata_row, csv_rows
                
                pos_np = np.frombuffer(bone_data[:6], dtype=np.float16, count=3).astype(float)
                csv_rows.append((
                    frame_id + 1, int(bone_id_int), get_bone_name(int(bone_id_int)),
                    round(pos_np[0], 6), round(pos_np[1], 6), round(pos_np[2], 6)
                ))
    return csv_metadata_row, csv_rows

def write_csv_file(output_filename, metadata_row, data_rows, label, logger=print):
    try:
        with open(output_filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(metadata_row)
            writer.writerow(["frame", "bone_id", "bone_name", "pos_x", "pos_y", "pos_z"])
            writer.writerows(data_rows)
        logger(f"-> {label} data and header saved to: {os.path.basename(output_filename)}")
        return True
    except Exception as e:
        logger(f"\nERROR: Could not write {label} CSV file: {e}")
        return False

def splicer_operation(file1_path, file2_path, range1_str, range2_str, logger=print, export_ext='.bytes'):
    """
    Splicer that handles multiple animation data segments from files with matching bone structures.
    Now handles cases where bone IDs are the same but in different orders.
    """
    logger("\n--- Starting SPLICER Operation ---")
    
    try:
        with open(file1_path, 'rb') as f:
            file1_data = f.read()
        with open(file2_path, 'rb') as f:
            file2_data = f.read()
        
        metadata1 = parse_header_metadata(BytesIO(file1_data))
        metadata2 = parse_header_metadata(BytesIO(file2_data))
        
        if not metadata1 or not metadata2:
            logger("CRITICAL ERROR: Could not parse headers from one or both files.")
            return False
        
        # MODIFIED: Check if bone sets are identical (same bones, regardless of order)
        bone_set1 = set(metadata1['bone_ids'])
        bone_set2 = set(metadata2['bone_ids'])
        
        if bone_set1 != bone_set2:
            logger("CRITICAL ERROR: Bone structures do not match.")
            logger(f"File 1 bones: {sorted(metadata1['bone_ids'])}")
            logger(f"File 2 bones: {sorted(metadata2['bone_ids'])}")
            return False
        
        # NEW: Check if bone orders are different and handle accordingly
        bone_orders_different = metadata1['bone_ids'] != metadata2['bone_ids']
        if bone_orders_different:
            logger("Note: Bone IDs are the same but in different orders. Adjusting data mapping...")
            
            # Create mapping from file2 bone order to file1 bone order
            bone_mapping = []
            for bone_id in metadata1['bone_ids']:
                bone_mapping.append(metadata2['bone_ids'].index(bone_id))
        
        start1, end1 = map(lambda x: int(x) - 1, range1_str.split('-'))
        start2, end2 = map(lambda x: int(x) - 1, range2_str.split('-'))
        
        if not (0 <= start1 <= end1 < metadata1['frames_length']):
            logger(f"CRITICAL ERROR: Invalid range for File 1: {range1_str}")
            return False
            
        if not (0 <= start2 <= end2 < metadata2['frames_length']):
            logger(f"CRITICAL ERROR: Invalid range for File 2: {range2_str}")
            return False
        
        bone_count = len(metadata1['bone_ids'])
        frame_size = bone_count * 12
        
        # Extract frames from File 1 (no changes needed)
        data1_start = metadata1['data_stream_position']
        frames1_data = b''
        for frame_idx in range(start1, end1 + 1):
            frame_start = data1_start + (frame_idx * frame_size)
            frame_end = frame_start + frame_size
            frames1_data += file1_data[frame_start:frame_end]
        
        # Extract and reorder frames from File 2 if bone orders are different
        data2_start = metadata2['data_stream_position']
        frames2_data = b''
        
        for frame_idx in range(start2, end2 + 1):
            frame_start = data2_start + (frame_idx * frame_size)
            frame_end = frame_start + frame_size
            frame_data = file2_data[frame_start:frame_end]
            
            if bone_orders_different:
                # Reorder bone data to match File 1's bone order
                reordered_frame_data = b''
                frame_stream = BytesIO(frame_data)
                
                # Read all bone data for this frame
                bone_data_list = []
                for _ in range(bone_count):
                    bone_data = frame_stream.read(12)
                    bone_data_list.append(bone_data)
                
                # Reorder according to mapping
                for target_index in range(bone_count):
                    source_index = bone_mapping[target_index]
                    reordered_frame_data += bone_data_list[source_index]
                
                frames2_data += reordered_frame_data
            else:
                # Bone orders are the same, use data as-is
                frames2_data += frame_data
        
        spliced_frame_data = frames1_data + frames2_data
        
        # Calculate frame counts for filename
        num_frames1 = end1 - start1 + 1
        num_frames2 = end2 - start2 + 1
        spliced_frames_count = num_frames1 + num_frames2
        
        logger(f"Spliced {spliced_frames_count} frames total:")
        logger(f"  - File 1: {num_frames1} frames ({range1_str})")
        logger(f"  - File 2: {num_frames2} frames ({range2_str})")
        if bone_orders_different:
            logger(f"  - Note: File 2 bone data was reordered to match File 1's bone structure")
        
        end_of_data1 = metadata1['data_stream_position'] + (metadata1['frames_length'] * frame_size)
        remaining_data1 = file1_data[end_of_data1:] if end_of_data1 < len(file1_data) else b''
        
        end_of_data2 = metadata2['data_stream_position'] + (metadata2['frames_length'] * frame_size)
        remaining_data2 = file2_data[end_of_data2:] if end_of_data2 < len(file2_data) else b''
        
        combined_remaining_data = remaining_data1 + remaining_data2
        
        if combined_remaining_data:
            logger(f"Added {len(combined_remaining_data)} bytes of trailing data (File1: {len(remaining_data1)} + File2: {len(remaining_data2)})")
        
        final_bytes = reconstruct_binary(metadata1, spliced_frames_count, spliced_frame_data, combined_remaining_data)
        
        # Generate dynamic tag for filename
        tag = f"SPLICER_{num_frames1}_{num_frames2}"
        output_filename = generate_output_filename(file1_path, tag, export_extension=export_ext)
        
        # === CRITICAL FIX: Write to VFS instead of regular file system ===
        try:
            with open(output_filename, 'wb') as f:
                f.write(final_bytes)
            logger(f"\nSplicer Complete!")
            logger(f"Output saved to: {os.path.basename(output_filename)}")
            
            return True
            
        except Exception as e:
            logger(f"ERROR writing output file: {e}")
            return False
        
    except Exception as e:
        logger(f"CRITICAL ERROR in splicer: {e}")
        import traceback
        logger(traceback.format_exc())
        return False

def main(cli_args=None, logger=print, get_operations=False):
    if get_operations:
        return OPERATION_MODE

    file_path = cli_args.get('file_path')
    selected_operation = cli_args.get('operation')
    export_ext = cli_args.get('export_extension', '.bytes')

    if selected_operation == 'SPLICER':
        file1_path, file2_path, range1_str, range2_str = \
            [cli_args.get(k) for k in ['file1', 'file2', 'range1', 'range2']]
        
        success = splicer_operation(
            file1_path, file2_path, range1_str, range2_str, 
            logger=logger, export_ext=export_ext
        )
        return
        
    if not file_path or not os.path.exists(file_path):
        logger(f"Error: File not found: {file_path}"); return

    with open(file_path, 'rb') as f: original_data_bytes = f.read()

    factor_n, factor_d, float_factor = 1, 1, 1.0; pelvis_initial_x = None; extra_op_params = {}

    try:
        if selected_operation in ['SHORTEN', 'LENGTHEN']:
            float_factor = float(cli_args.get('factor'))
            if selected_operation == 'SHORTEN':
                factor_n, factor_d = get_decimation_params(float_factor, logger)
                extra_op_params['float_factor_str'] = f"{float_factor:.1f}".replace('.', '_')
            else:
                factor_n = int(round(float_factor))
        elif selected_operation == 'DASH':
            factor_n = float(cli_args.get('offset_factor'))
            factor_d = 1 if cli_args.get('direction') == 'Towards' else -1
        elif selected_operation == 'SPLIT_DASH':
            metadata = parse_header_metadata(BytesIO(original_data_bytes))
            if not metadata: logger("ERROR: Cannot read animation header."); return
            phase1_frames = int(cli_args.get('phase1_frames'))
            if not (0 <= phase1_frames <= metadata['frames_length']):
                logger(f"ERROR: 'Phase 1 Frames' ({phase1_frames}) must be between 0 and {metadata['frames_length']}."); return
            extra_op_params = {k: cli_args.get(k) for k in ['p1_offset', 'p2_offset']}
            extra_op_params['order'] = 'towards_first' if cli_args.get('order') == 'Towards' else 'away_first'
            extra_op_params['phase1_frames'] = phase1_frames
        elif selected_operation == 'BIRTH_LOCATION':
            metadata = parse_header_metadata(BytesIO(original_data_bytes))
            data_stream = BytesIO(original_data_bytes); data_stream.seek(metadata['data_stream_position'])
            _, pelvis_initial_x = check_pelvis_x_static(data_stream, metadata['frames_length'], metadata['bone_ids'])
            factor_n = float(cli_args.get('total_offset'))
            factor_d = 1 if cli_args.get('direction') == 'Towards' else -1
        elif selected_operation in ['TRIMMER', 'AXIS_ADDER', 'AXIS_SCALER']:
            extra_op_params = {k: cli_args.get(k) for k in cli_args if k not in ['file_path', 'operation', 'export_extension', 'save_csvs']}
    except (ValueError, TypeError) as e:
        logger(f"Error: Invalid parameter format. Details: {e}"); return

    if selected_operation == 'EXTRACT_CSV':
        meta_row, csv_data = extract_data_and_metadata(BytesIO(original_data_bytes))
        output_csv_path = generate_output_filename(file_path, "EXTRACTED", is_binary_output=False)
        write_csv_file(output_csv_path, meta_row, csv_data, "Extracted", logger)
        logger("\nProcess complete."); return

    success, final_modified_bytes, tag = modify_and_repack_animation_data(
        file_path, original_data_bytes, selected_operation, factor_n, factor_d, 
        logger=logger, initial_x=pelvis_initial_x, **extra_op_params
    )

    if success:
        output_binary_filename = generate_output_filename(file_path, tag, is_binary_output=True, export_extension=export_ext)
        try:
            # === CRITICAL FIX: Write to VFS ===
            with open(output_binary_filename, 'wb') as f: 
                f.write(final_modified_bytes)
            logger(f"\n--- Repack Complete ---")
            logger(f"-> Modified animation saved to: {os.path.basename(output_binary_filename)}")
            
            if cli_args.get('save_csvs', True):
                meta_row, csv_data = extract_data_and_metadata(BytesIO(original_data_bytes))
                mod_meta_row, mod_csv_data = extract_data_and_metadata(BytesIO(final_modified_bytes))
                if mod_csv_data:
                    orig_csv_path = generate_output_filename(file_path, "ORIGINAL", False)
                    mod_csv_path = generate_output_filename(file_path, tag, False)
                    write_csv_file(orig_csv_path, meta_row, csv_data, "Original", logger)
                    write_csv_file(mod_csv_path, mod_meta_row, mod_csv_data, tag, logger)
        except Exception as e:
            logger(f"\nERROR: Could not write modified binary file: {e}")
            
        logger("\nProcess complete.")

if __name__ == "__main__":
    print("This is the core logic script. Please run 'runner_ui.py' to use the graphical interface.")
