#!/usr/bin/env python3
"""
Extract a random screenshot from a video file and save it as an image.
"""
import os
import random
import cv2

def extract_random_screenshot(video_path, output_path):
    """Extract a random frame from video and save as image."""
    
    # Check if video file exists
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Load the video
    print(f"Loading video: {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    # Get video properties
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = frame_count / fps
    
    print(f"Video duration: {duration:.2f} seconds")
    print(f"Total frames: {frame_count}")
    print(f"FPS: {fps:.2f}")
    
    # Choose a random frame between 10% and 90% of the video
    # This avoids potential intro/outro screens
    start_frame = int(frame_count * 0.1)
    end_frame = int(frame_count * 0.9)
    random_frame = random.randint(start_frame, end_frame)
    random_time = random_frame / fps
    
    print(f"Extracting frame {random_frame} at {random_time:.2f} seconds")
    
    # Set the frame position
    cap.set(cv2.CAP_PROP_POS_FRAMES, random_frame)
    
    # Read the frame
    ret, frame = cap.read()
    
    if not ret:
        raise ValueError(f"Could not read frame {random_frame}")
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the frame as an image
    # OpenCV uses BGR, but we'll save it as is since it's just for demo
    success = cv2.imwrite(output_path, frame)
    
    if not success:
        raise ValueError(f"Could not save image to {output_path}")
    
    print(f"Screenshot saved to: {output_path}")
    
    # Close the video capture
    cap.release()
    
    return output_path

if __name__ == "__main__":
    video_file = r"C:\Users\yeshw\Downloads\Compressed\bck_alm_1\vid op\Yeshwanth_C_R_1.mp4"
    output_file = "docs/demo-screenshot.png"
    
    try:
        extract_random_screenshot(video_file, output_file)
        print("Screenshot extraction completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
