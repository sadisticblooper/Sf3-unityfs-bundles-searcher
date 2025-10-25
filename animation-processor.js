// Bone mapping
export const BONE_MAP = {
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
};

const EXPECTED_HEADER = 457546134634734n;

// Animation Processor
export class AnimationProcessor {
    constructor(logElement) {
        this.logElement = logElement;
        this.BONE_MAP = BONE_MAP;
    }

    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const styledMessage = `[${timestamp}] <span class="log-${type}">${message}</span>`;
        this.logElement.innerHTML += styledMessage + '\n';
        this.logElement.scrollTop = this.logElement.scrollHeight;
    }

    clearLog() {
        this.logElement.textContent = '';
    }

    updateProgress(percent) {
        const progressFill = document.getElementById('progressFill');
        const progressContainer = document.getElementById('progressContainer');
        
        if (percent > 0) {
            progressContainer.style.display = 'block';
            progressFill.style.width = percent + '%';
        } else {
            progressContainer.style.display = 'none';
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Core parsing function
    parseHeaderMetadata(dataView) {
        let offset = 0;

        // Read header
        if (dataView.byteLength < 8) return null;
        const header = dataView.getBigUint64(offset, true);
        offset += 8;

        if (header !== EXPECTED_HEADER) {
            this.log('Warning: Unexpected file header', 'warning');
        }

        // Read garbage size
        if (dataView.byteLength < offset + 2) return null;
        const garbageSize = dataView.getInt16(offset, true);
        offset += 2;

        // Skip garbage data
        const garbageDataSize = garbageSize * 8;
        if (dataView.byteLength < offset + garbageDataSize) return null;
        offset += garbageDataSize;

        // Read frame count
        if (dataView.byteLength < offset + 4) return null;
        const framesLength = dataView.getInt32(offset, true);
        offset += 4;

        // Read bone count
        if (dataView.byteLength < offset + 4) return null;
        const boneIdsLength = dataView.getInt32(offset, true);
        offset += 4;

        // Read bone IDs
        if (dataView.byteLength < offset + boneIdsLength * 2) return null;
        const boneIds = [];
        for (let i = 0; i < boneIdsLength; i++) {
            boneIds.push(dataView.getInt16(offset, true));
            offset += 2;
        }

        return {
            header,
            framesLength,
            boneIds,
            boneIdsLength,
            garbageSize,
            dataOffset: offset,
            totalSize: dataView.byteLength
        };
    }

    parseAnimationData(arrayBuffer, filename) {
        try {
            const dataView = new DataView(arrayBuffer);
            const metadata = this.parseHeaderMetadata(dataView);
            
            if (!metadata) {
                this.log('✗ Error: Invalid file format or corrupted data', 'error');
                return null;
            }

            // Read the entire animation data block at once
            const boneCount = metadata.boneIds.length;
            const frameSizeBytes = boneCount * 12;
            const expectedAnimationBytes = metadata.framesLength * frameSizeBytes;
            
            const animationDataBytes = arrayBuffer.slice(
                metadata.dataOffset, 
                metadata.dataOffset + expectedAnimationBytes
            );

            const remainingData = arrayBuffer.slice(metadata.dataOffset + expectedAnimationBytes);

            this.log(`✓ File parsed successfully: ${filename}`, 'success');
            this.log(`• Frames: ${metadata.framesLength}`, 'info');
            this.log(`• Bones: ${metadata.boneIdsLength}`, 'info');
            this.log(`• Bone IDs: [${metadata.boneIds.join(', ')}]`, 'info');
            this.log(`• Animation data: ${this.formatFileSize(animationDataBytes.byteLength)}`, 'info');
            if (remainingData.byteLength > 0) {
                this.log(`• Trailing data: ${this.formatFileSize(remainingData.byteLength)}`, 'info');
            }

            return {
                ...metadata,
                arrayBuffer,
                dataView,
                animationDataBytes,
                remainingData,
                frameSizeBytes
            };

        } catch (error) {
            this.log(`✗ Error parsing animation data: ${error}`, 'error');
            return null;
        }
    }

    // Float16 conversion functions
    readFloat16(dataView, offset) {
        const uint16 = dataView.getUint16(offset, true);
        return this.float16ToFloat32(uint16);
    }

    writeFloat16(dataView, offset, value) {
        const uint16 = this.float32ToFloat16(value);
        dataView.setUint16(offset, uint16, true);
    }

    float16ToFloat32(uint16) {
        const sign = (uint16 & 0x8000) ? -1 : 1;
        const exponent = (uint16 & 0x7C00) >> 10;
        const fraction = uint16 & 0x03FF;

        if (exponent === 0) {
            return sign * Math.pow(2, -14) * (fraction / 1024);
        } else if (exponent === 0x1F) {
            return fraction ? NaN : sign * Infinity;
        }

        return sign * Math.pow(2, exponent - 15) * (1 + fraction / 1024);
    }

    float32ToFloat16(value) {
        const float32 = new Float32Array([value]);
        const uint32 = new Uint32Array(float32.buffer)[0];
        
        const sign = (uint32 >> 31) & 0x1;
        let exponent = ((uint32 >> 23) & 0xFF) - 127;
        const fraction = (uint32 >> 13) & 0x3FF;

        // Handle edge cases
        if (exponent > 15) {
            return (sign << 15) | 0x7C00; // Infinity
        }
        if (exponent < -14) {
            return (sign << 15); // Zero (subnormal becomes zero)
        }

        exponent += 15;
        return (sign << 15) | (exponent << 10) | fraction;
    }

    // Process bone data with modifier
    processBoneData(boneData, modifier = null) {
        if (boneData.byteLength < 12) return null;

        const dataView = new DataView(boneData);
        const posX = this.readFloat16(dataView, 0);
        const posY = this.readFloat16(dataView, 2);
        const posZ = this.readFloat16(dataView, 4);

        let newPos = [posX, posY, posZ];
        if (modifier) {
            newPos = modifier(newPos);
        }

        const newBuffer = new ArrayBuffer(12);
        const newView = new DataView(newBuffer);
        
        this.writeFloat16(newView, 0, newPos[0]);
        this.writeFloat16(newView, 2, newPos[1]);
        this.writeFloat16(newView, 4, newPos[2]);
        
        // Copy rotation data unchanged (bytes 6-11)
        for (let i = 6; i < 12; i++) {
            newView.setUint8(i, dataView.getUint8(i));
        }

        return newBuffer;
    }

    // Operation implementations
    shortenAnimation(animationData, factorN, factorD) {
        const { framesLength, boneIds, animationDataBytes } = animationData;
        const boneCount = boneIds.length;
        const frameSize = boneCount * 12;
        
        const frameDataView = new DataView(animationDataBytes);
        let newFramesLength = 0;
        const outputChunks = [];

        this.log(`Shortening: keep ${factorD} of every ${factorN} frames`, 'info');
        this.updateProgress(10);

        for (let frameId = 0; frameId < framesLength; frameId++) {
            const keepFrame = ((frameId % factorN) < factorD);
            
            if (keepFrame) {
                const frameOffset = frameId * frameSize;
                const frameData = animationDataBytes.slice(frameOffset, frameOffset + frameSize);
                
                // Process each bone in the frame
                const processedFrameData = new ArrayBuffer(frameSize);
                const processedView = new DataView(processedFrameData);
                let processedOffset = 0;
                
                for (let boneIdx = 0; boneIdx < boneCount; boneIdx++) {
                    const boneOffset = frameOffset + (boneIdx * 12);
                    const boneData = animationDataBytes.slice(boneOffset, boneOffset + 12);
                    const processedBoneData = this.processBoneData(boneData);
                    
                    if (processedBoneData) {
                        const boneView = new DataView(processedBoneData);
                        for (let i = 0; i < 12; i++) {
                            processedView.setUint8(processedOffset + i, boneView.getUint8(i));
                        }
                        processedOffset += 12;
                    }
                }
                
                outputChunks.push(processedFrameData);
                newFramesLength++;
            }

            // Update progress
            if (frameId % 10 === 0) {
                const progress = 10 + (frameId / framesLength) * 80;
                this.updateProgress(progress);
            }
        }

        this.updateProgress(90);
        return { 
            newFramesLength, 
            data: this.concatArrayBuffers(outputChunks),
            remainingData: animationData.remainingData
        };
    }

    lengthenAnimation(animationData, factor) {
        const { framesLength, boneIds, animationDataBytes } = animationData;
        const boneCount = boneIds.length;
        const frameSize = boneCount * 12;
        
        const outputChunks = [];

        this.log(`Lengthening: duplicate each frame ${factor} times`, 'info');
        this.updateProgress(10);

        for (let frameId = 0; frameId < framesLength; frameId++) {
            const frameOffset = frameId * frameSize;
            const frameData = animationDataBytes.slice(frameOffset, frameOffset + frameSize);
            
            // Process and clean the frame data once before duplicating
            const processedFrameData = new ArrayBuffer(frameSize);
            const processedView = new DataView(processedFrameData);
            const frameDataView = new DataView(frameData);
            
            for (let boneIdx = 0; boneIdx < boneCount; boneIdx++) {
                const boneOffset = boneIdx * 12;
                const boneData = frameData.slice(boneOffset, boneOffset + 12);
                const processedBoneData = this.processBoneData(boneData);
                
                if (processedBoneData) {
                    const boneView = new DataView(processedBoneData);
                    for (let i = 0; i < 12; i++) {
                        processedView.setUint8(boneOffset + i, boneView.getUint8(i));
                    }
                }
            }
            
            // Write the cleaned frame data 'factor' times
            for (let i = 0; i < factor; i++) {
                outputChunks.push(processedFrameData);
            }

            // Update progress
            if (frameId % 10 === 0) {
                const progress = 10 + (frameId / framesLength) * 80;
                this.updateProgress(progress);
            }
        }

        this.updateProgress(90);
        return { 
            newFramesLength: framesLength * factor, 
            data: this.concatArrayBuffers(outputChunks),
            remainingData: animationData.remainingData
        };
    }

    xDoubleAnimation(animationData) {
        const { framesLength, boneIds, animationDataBytes } = animationData;
        const boneCount = boneIds.length;
        const frameSize = boneCount * 12;
        
        const outputChunks = [];

        this.log('Doubling X coordinates for all bones', 'info');
        this.updateProgress(10);

        for (let frameId = 0; frameId < framesLength; frameId++) {
            const frameOffset = frameId * frameSize;
            const frameBuffer = new ArrayBuffer(frameSize);
            const frameView = new DataView(frameBuffer);

            for (let boneIdx = 0; boneIdx < boneCount; boneIdx++) {
                const boneOffset = frameOffset + (boneIdx * 12);
                const boneData = animationDataBytes.slice(boneOffset, boneOffset + 12);
                const boneDataView = new DataView(boneData);
                
                // Double X coordinate
                const modifier = (pos) => {
                    pos[0] *= 2.0;
                    return pos;
                };
                
                const processedBoneData = this.processBoneData(boneData, modifier);
                
                if (processedBoneData) {
                    const processedView = new DataView(processedBoneData);
                    const targetOffset = boneIdx * 12;
                    for (let i = 0; i < 12; i++) {
                        frameView.setUint8(targetOffset + i, processedView.getUint8(i));
                    }
                }
            }

            outputChunks.push(frameBuffer);

            // Update progress
            if (frameId % 10 === 0) {
                const progress = 10 + (frameId / framesLength) * 80;
                this.updateProgress(progress);
            }
        }

        this.updateProgress(90);
        return { 
            newFramesLength: framesLength, 
            data: this.concatArrayBuffers(outputChunks),
            remainingData: animationData.remainingData
        };
    }

    dashAnimation(animationData, offsetFactor, directionSign) {
        const { framesLength, boneIds, animationDataBytes } = animationData;
        const boneCount = boneIds.length;
        const frameSize = boneCount * 12;
        const maxFrameIndex = framesLength - 1;
        
        const outputChunks = [];
        const pelvisIndex = boneIds.indexOf(0);

        this.log(`Applying dash: offset=${offsetFactor}, direction=${directionSign > 0 ? 'Towards' : 'Away'}`, 'info');
        this.updateProgress(10);

        for (let frameId = 0; frameId < framesLength; frameId++) {
            const currentOffset = (maxFrameIndex - frameId) * offsetFactor * directionSign;
            const frameOffset = frameId * frameSize;
            const frameBuffer = new ArrayBuffer(frameSize);
            const frameView = new DataView(frameBuffer);

            for (let boneIdx = 0; boneIdx < boneCount; boneIdx++) {
                const boneOffset = frameOffset + (boneIdx * 12);
                const boneData = animationDataBytes.slice(boneOffset, boneOffset + 12);
                
                let modifier = null;
                // Apply offset only to pelvis (bone ID 0)
                if (boneIds[boneIdx] === 0) {
                    modifier = (pos) => {
                        pos[0] += currentOffset;
                        return pos;
                    };
                }
                
                const processedBoneData = this.processBoneData(boneData, modifier);
                
                if (processedBoneData) {
                    const processedView = new DataView(processedBoneData);
                    const targetOffset = boneIdx * 12;
                    for (let i = 0; i < 12; i++) {
                        frameView.setUint8(targetOffset + i, processedView.getUint8(i));
                    }
                }
            }

            outputChunks.push(frameBuffer);

            // Update progress
            if (frameId % 10 === 0) {
                const progress = 10 + (frameId / framesLength) * 80;
                this.updateProgress(progress);
            }
        }

        this.updateProgress(90);
        return { 
            newFramesLength: framesLength, 
            data: this.concatArrayBuffers(outputChunks),
            remainingData: animationData.remainingData
        };
    }

    birthLocationAnimation(animationData, totalOffset, directionSign) {
        const { framesLength, boneIds, animationDataBytes } = animationData;
        const boneCount = boneIds.length;
        const frameSize = boneCount * 12;
        const RAMP_UP_DURATION = 30;
        const effectiveRampFrames = Math.min(RAMP_UP_DURATION, framesLength);
        const lerpDivisor = effectiveRampFrames > 1 ? effectiveRampFrames - 1 : 1;
        const finalSignedOffset = totalOffset * directionSign;
        
        // Get initial pelvis X from first frame
        const pelvisIndex = boneIds.indexOf(0);
        let initialPelvisX = 0;
        if (pelvisIndex >= 0) {
            const firstFramePelvisOffset = pelvisIndex * 12;
            const boneData = animationDataBytes.slice(firstFramePelvisOffset, firstFramePelvisOffset + 12);
            const boneDataView = new DataView(boneData);
            initialPelvisX = this.readFloat16(boneDataView, 0);
        }

        const outputChunks = [];

        this.log(`Birth location: total offset=${totalOffset}, direction=${directionSign > 0 ? 'Towards' : 'Away'}`, 'info');
        this.updateProgress(10);

        for (let frameId = 0; frameId < framesLength; frameId++) {
            let currentOffset = 0.0;
            if (frameId < effectiveRampFrames) {
                const t = frameId / lerpDivisor;
                currentOffset = finalSignedOffset * t;
            } else {
                currentOffset = finalSignedOffset;
            }

            const frameOffset = frameId * frameSize;
            const frameBuffer = new ArrayBuffer(frameSize);
            const frameView = new DataView(frameBuffer);

            for (let boneIdx = 0; boneIdx < boneCount; boneIdx++) {
                const boneOffset = frameOffset + (boneIdx * 12);
                const boneData = animationDataBytes.slice(boneOffset, boneOffset + 12);
                
                let modifier = null;
                // Apply to pelvis only
                if (boneIds[boneIdx] === 0) {
                    modifier = (pos) => {
                        pos[0] = initialPelvisX + currentOffset;
                        return pos;
                    };
                }
                
                const processedBoneData = this.processBoneData(boneData, modifier);
                
                if (processedBoneData) {
                    const processedView = new DataView(processedBoneData);
                    const targetOffset = boneIdx * 12;
                    for (let i = 0; i < 12; i++) {
                        frameView.setUint8(targetOffset + i, processedView.getUint8(i));
                    }
                }
            }

            outputChunks.push(frameBuffer);

            // Update progress
            if (frameId % 10 === 0) {
                const progress = 10 + (frameId / framesLength) * 80;
                this.updateProgress(progress);
            }
        }

        this.updateProgress(90);
        return { 
            newFramesLength: framesLength, 
            data: this.concatArrayBuffers(outputChunks),
            remainingData: animationData.remainingData
        };
    }

    trimmerAnimation(animationData, startFrame, endFrame) {
        const { framesLength, boneIds, animationDataBytes } = animationData;
        const boneCount = boneIds.length;
        const frameSize = boneCount * 12;
        
        let newFramesLength = 0;
        const outputChunks = [];

        this.log(`Trimming: removing frames ${startFrame + 1} to ${endFrame + 1}`, 'info');
        this.updateProgress(10);

        for (let frameId = 0; frameId < framesLength; frameId++) {
            if (frameId >= startFrame && frameId <= endFrame) {
                continue;
            }

            const frameOffset = frameId * frameSize;
            const frameData = animationDataBytes.slice(frameOffset, frameOffset + frameSize);
            
            // Process the frame to ensure clean data
            const processedFrameData = new ArrayBuffer(frameSize);
            const processedView = new DataView(processedFrameData);
            const frameDataView = new DataView(frameData);
            
            for (let boneIdx = 0; boneIdx < boneCount; boneIdx++) {
                const boneOffset = boneIdx * 12;
                const boneData = frameData.slice(boneOffset, boneOffset + 12);
                const processedBoneData = this.processBoneData(boneData);
                
                if (processedBoneData) {
                    const boneView = new DataView(processedBoneData);
                    for (let i = 0; i < 12; i++) {
                        processedView.setUint8(boneOffset + i, boneView.getUint8(i));
                    }
                }
            }
            
            outputChunks.push(processedFrameData);
            newFramesLength++;

            // Update progress
            if (frameId % 10 === 0) {
                const progress = 10 + (frameId / framesLength) * 80;
                this.updateProgress(progress);
            }
        }

        this.updateProgress(90);
        return { 
            newFramesLength, 
            data: this.concatArrayBuffers(outputChunks),
            remainingData: animationData.remainingData
        };
    }

    axisAdderAnimation(animationData, xOffset, yOffset, zOffset, boneId) {
        const { framesLength, boneIds, animationDataBytes } = animationData;
        const boneCount = boneIds.length;
        const frameSize = boneCount * 12;
        
        const outputChunks = [];

        this.log(`Axis adder: X=${xOffset}, Y=${yOffset}, Z=${zOffset}, Bone=${boneId}`, 'info');
        this.updateProgress(10);

        for (let frameId = 0; frameId < framesLength; frameId++) {
            const frameOffset = frameId * frameSize;
            const frameBuffer = new ArrayBuffer(frameSize);
            const frameView = new DataView(frameBuffer);

            for (let boneIdx = 0; boneIdx < boneCount; boneIdx++) {
                const boneOffset = frameOffset + (boneIdx * 12);
                const boneData = animationDataBytes.slice(boneOffset, boneOffset + 12);
                
                let modifier = null;
                // Apply if bone matches or if boneId is -1 (all bones)
                if (boneId === -1 || boneIds[boneIdx] === parseInt(boneId)) {
                    modifier = (pos) => {
                        pos[0] += parseFloat(xOffset);
                        pos[1] += parseFloat(yOffset);
                        pos[2] += parseFloat(zOffset);
                        return pos;
                    };
                }
                
                const processedBoneData = this.processBoneData(boneData, modifier);
                
                if (processedBoneData) {
                    const processedView = new DataView(processedBoneData);
                    const targetOffset = boneIdx * 12;
                    for (let i = 0; i < 12; i++) {
                        frameView.setUint8(targetOffset + i, processedView.getUint8(i));
                    }
                }
            }

            outputChunks.push(frameBuffer);

            // Update progress
            if (frameId % 10 === 0) {
                const progress = 10 + (frameId / framesLength) * 80;
                this.updateProgress(progress);
            }
        }

        this.updateProgress(90);
        return { 
            newFramesLength: framesLength, 
            data: this.concatArrayBuffers(outputChunks),
            remainingData: animationData.remainingData
        };
    }

    axisScalerAnimation(animationData, scaleFactor, targetBoneIds) {
        const { framesLength, boneIds, animationDataBytes } = animationData;
        const boneCount = boneIds.length;
        const frameSize = boneCount * 12;
        const PROGRESSIVE_FRAMES = 10;
        const progressiveFrames = Math.min(PROGRESSIVE_FRAMES, framesLength);
        
        // Calculate progressive scale factors
        const progressiveFactors = [];
        for (let frameIdx = 0; frameIdx < framesLength; frameIdx++) {
            if (frameIdx < progressiveFrames && progressiveFrames > 1) {
                const t = frameIdx / (progressiveFrames - 1);
                progressiveFactors.push(1.0 + (scaleFactor - 1.0) * t);
            } else {
                progressiveFactors.push(scaleFactor);
            }
        }

        const outputChunks = [];

        this.log(`Axis scaler: factor=${scaleFactor}, bones=${targetBoneIds.length > 0 ? targetBoneIds.join(',') : 'all'}`, 'info');
        this.updateProgress(10);

        for (let frameId = 0; frameId < framesLength; frameId++) {
            const currentScale = progressiveFactors[frameId];
            const frameOffset = frameId * frameSize;
            const frameBuffer = new ArrayBuffer(frameSize);
            const frameView = new DataView(frameBuffer);

            for (let boneIdx = 0; boneIdx < boneCount; boneIdx++) {
                const boneOffset = frameOffset + (boneIdx * 12);
                const boneData = animationDataBytes.slice(boneOffset, boneOffset + 12);
                
                let modifier = null;
                // Apply scaling if bone is in target list or if list is empty (all bones)
                if (targetBoneIds.length === 0 || targetBoneIds.includes(boneIds[boneIdx])) {
                    modifier = (pos) => {
                        pos[0] *= currentScale;
                        pos[1] *= currentScale;
                        pos[2] *= currentScale;
                        return pos;
                    };
                }
                
                const processedBoneData = this.processBoneData(boneData, modifier);
                
                if (processedBoneData) {
                    const processedView = new DataView(processedBoneData);
                    const targetOffset = boneIdx * 12;
                    for (let i = 0; i < 12; i++) {
                        frameView.setUint8(targetOffset + i, processedView.getUint8(i));
                    }
                }
            }

            outputChunks.push(frameBuffer);

            // Update progress
            if (frameId % 10 === 0) {
                const progress = 10 + (frameId / framesLength) * 80;
                this.updateProgress(progress);
            }
        }

        this.updateProgress(90);
        return { 
            newFramesLength: framesLength, 
            data: this.concatArrayBuffers(outputChunks),
            remainingData: animationData.remainingData
        };
    }

    async splicerAnimation(anim1, anim2, range1Str, range2Str) {
        this.log('Starting SPLICER operation...', 'info');
        this.updateProgress(10);

        // Check bone structure compatibility
        const boneSet1 = new Set(anim1.boneIds);
        const boneSet2 = new Set(anim2.boneIds);
        
        if (boneSet1.size !== boneSet2.size || ![...boneSet1].every(bone => boneSet2.has(bone))) {
            this.log('✗ Error: Bone structures do not match', 'error');
            this.log(`File 1 bones: [${anim1.boneIds.join(', ')}]`, 'error');
            this.log(`File 2 bones: [${anim2.boneIds.join(', ')}]`, 'error');
            return null;
        }

        // Parse ranges
        const [start1, end1] = range1Str.split('-').map(x => parseInt(x) - 1);
        const [start2, end2] = range2Str.split('-').map(x => parseInt(x) - 1);

        if (start1 < 0 || end1 >= anim1.framesLength || start1 > end1) {
            this.log(`✗ Error: Invalid range for File 1: ${range1Str}`, 'error');
            return null;
        }
        if (start2 < 0 || end2 >= anim2.framesLength || start2 > end2) {
            this.log(`✗ Error: Invalid range for File 2: ${range2Str}`, 'error');
            return null;
        }

        const boneCount = anim1.boneIds.length;
        const frameSize = boneCount * 12;
        const numFrames1 = end1 - start1 + 1;
        const numFrames2 = end2 - start2 + 1;
        const totalFrames = numFrames1 + numFrames2;

        this.log(`Splicing ${numFrames1} frames from File 1 and ${numFrames2} frames from File 2`, 'info');
        this.updateProgress(30);

        // Extract frames from File 1
        const frames1 = [];
        for (let frame = start1; frame <= end1; frame++) {
            const offset = frame * frameSize;
            const frameData = anim1.animationDataBytes.slice(offset, offset + frameSize);
            
            // Process frame to ensure clean data
            const processedFrame = new ArrayBuffer(frameSize);
            const processedView = new DataView(processedFrame);
            const frameView = new DataView(frameData);
            
            for (let boneIdx = 0; boneIdx < boneCount; boneIdx++) {
                const boneOffset = boneIdx * 12;
                const boneData = frameData.slice(boneOffset, boneOffset + 12);
                const processedBoneData = this.processBoneData(boneData);
                
                if (processedBoneData) {
                    const boneView = new DataView(processedBoneData);
                    for (let i = 0; i < 12; i++) {
                        processedView.setUint8(boneOffset + i, boneView.getUint8(i));
                    }
                }
            }
            frames1.push(processedFrame);
        }

        this.updateProgress(60);

        // Extract frames from File 2 (handle bone order differences)
        const frames2 = [];
        const boneOrderDifferent = JSON.stringify(anim1.boneIds) !== JSON.stringify(anim2.boneIds);
        
        if (boneOrderDifferent) {
            this.log('Note: Bone orders differ, reordering File 2 data', 'warning');
            // Create mapping from file2 to file1 bone order
            const boneMapping = anim1.boneIds.map(boneId => anim2.boneIds.indexOf(boneId));
            
            for (let frame = start2; frame <= end2; frame++) {
                const frameBuffer = new ArrayBuffer(frameSize);
                const frameView = new DataView(frameBuffer);
                const sourceOffset = frame * frameSize;

                for (let targetIdx = 0; targetIdx < boneCount; targetIdx++) {
                    const sourceIdx = boneMapping[targetIdx];
                    const sourceBoneOffset = sourceOffset + (sourceIdx * 12);
                    const targetBoneOffset = targetIdx * 12;

                    const boneData = anim2.animationDataBytes.slice(sourceBoneOffset, sourceBoneOffset + 12);
                    const processedBoneData = this.processBoneData(boneData);
                    
                    if (processedBoneData) {
                        const boneView = new DataView(processedBoneData);
                        for (let i = 0; i < 12; i++) {
                            frameView.setUint8(targetBoneOffset + i, boneView.getUint8(i));
                        }
                    }
                }
                frames2.push(frameBuffer);
            }
        } else {
            // Same bone order, direct copy with processing
            for (let frame = start2; frame <= end2; frame++) {
                const offset = frame * frameSize;
                const frameData = anim2.animationDataBytes.slice(offset, offset + frameSize);
                
                // Process frame to ensure clean data
                const processedFrame = new ArrayBuffer(frameSize);
                const processedView = new DataView(processedFrame);
                const frameView = new DataView(frameData);
                
                for (let boneIdx = 0; boneIdx < boneCount; boneIdx++) {
                    const boneOffset = boneIdx * 12;
                    const boneData = frameData.slice(boneOffset, boneOffset + 12);
                    const processedBoneData = this.processBoneData(boneData);
                    
                    if (processedBoneData) {
                        const boneView = new DataView(processedBoneData);
                        for (let i = 0; i < 12; i++) {
                            processedView.setUint8(boneOffset + i, boneView.getUint8(i));
                        }
                    }
                }
                frames2.push(processedFrame);
            }
        }

        this.updateProgress(90);

        // Combine frames
        const splicedData = this.concatArrayBuffers([...frames1, ...frames2]);

        // Combine remaining data from both files
        const combinedRemainingData = this.concatArrayBuffers([
            anim1.remainingData,
            anim2.remainingData
        ]);

        return {
            metadata: anim1,
            newFramesLength: totalFrames,
            data: splicedData,
            remainingData: combinedRemainingData,
            tag: `SPLICER_${numFrames1}_${numFrames2}`
        };
    }

    // Extract CSV data
    extractCSV(animationData) {
        const { framesLength, boneIds, animationDataBytes } = animationData;
        const boneCount = boneIds.length;
        const frameSize = boneCount * 12;
        const csvRows = [['frame', 'bone_id', 'bone_name', 'pos_x', 'pos_y', 'pos_z']];

        this.log('Extracting CSV data...', 'info');
        this.updateProgress(10);

        for (let frame = 0; frame < framesLength; frame++) {
            for (let boneIdx = 0; boneIdx < boneCount; boneIdx++) {
                const boneOffset = (frame * frameSize) + (boneIdx * 12);
                const boneData = animationDataBytes.slice(boneOffset, boneOffset + 12);
                const boneDataView = new DataView(boneData);
                
                const posX = this.readFloat16(boneDataView, 0);
                const posY = this.readFloat16(boneDataView, 2);
                const posZ = this.readFloat16(boneDataView, 4);
                
                const boneId = boneIds[boneIdx];
                const boneName = this.BONE_MAP[boneId] || `Bone_${boneId}`;
                
                csvRows.push([
                    frame + 1,
                    boneId,
                    boneName,
                    posX.toFixed(6),
                    posY.toFixed(6),
                    posZ.toFixed(6)
                ]);
            }

            // Update progress
            if (frame % 10 === 0) {
                const progress = 10 + (frame / framesLength * 80);
                this.updateProgress(progress);
            }
        }

        this.updateProgress(100);
        this.log(`✓ CSV extraction complete: ${csvRows.length - 1} data rows`, 'success');
        return csvRows;
    }

    // Reconstruct binary file with new frame data
    reconstructBinary(metadata, newFramesLength, frameData, remainingData) {
        const { dataView, dataOffset, garbageSize } = metadata;
        const headerSize = dataOffset;
        
        // Create new buffer
        const newBuffer = new ArrayBuffer(headerSize + frameData.byteLength + (remainingData ? remainingData.byteLength : 0));
        const newView = new DataView(newBuffer);

        // Copy original header
        for (let i = 0; i < headerSize; i++) {
            newView.setUint8(i, dataView.getUint8(i));
        }

        // Update frame count in header (at position after garbage data)
        const framesLengthPosition = 8 + 2 + (garbageSize * 8);
        newView.setInt32(framesLengthPosition, newFramesLength, true);

        // Copy new frame data
        const frameBytes = new Uint8Array(frameData);
        const newBytes = new Uint8Array(newBuffer);
        newBytes.set(frameBytes, headerSize);

        // Copy remaining data if it exists
        if (remainingData && remainingData.byteLength > 0) {
            const remainingBytes = new Uint8Array(remainingData);
            newBytes.set(remainingBytes, headerSize + frameData.byteLength);
        }

        return newBuffer;
    }

    // Utility function to concatenate ArrayBuffers
    concatArrayBuffers(buffers) {
        const totalLength = buffers.reduce((sum, buffer) => sum + buffer.byteLength, 0);
        const result = new Uint8Array(totalLength);
        let offset = 0;
        
        for (const buffer of buffers) {
            result.set(new Uint8Array(buffer), offset);
            offset += buffer.byteLength;
        }
        
        return result.buffer;
    }

    // Download file
    downloadFile(data, filename, contentType) {
        try {
            const blob = new Blob([data], { type: contentType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.log(`✓ Download started: ${filename}`, 'success');
            return true;
        } catch (error) {
            this.log(`✗ Download failed: ${error}`, 'error');
            return false;
        }
    }
}
