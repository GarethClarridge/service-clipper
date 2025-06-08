import os
import json
import shutil
from dotenv import load_dotenv
from job_handler.handler import process_job # Import the new process_job function

# Attempt to import ffmpeg for dummy video creation. If not available, user must provide video.
try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False

def create_dummy_video_if_not_exists(video_path: str, duration: int = 20):
    """
    Creates a dummy MP4 video file if it doesn't already exist.
    Requires ffmpeg to be installed and accessible.
    """
    if os.path.exists(video_path):
        print(f"Video file already exists: {video_path}")
        return True

    if not FFMPEG_AVAILABLE:
        print(f"INFO: ffmpeg-python is not installed. Cannot create dummy video: {video_path}")
        print(f"Please place a video file at '{video_path}' manually to run the sample job.")
        return False

    print(f"Attempting to create dummy video: {video_path} (Duration: {duration}s)")
    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(video_path)
        if parent_dir: # Check if parent_dir is not an empty string (e.g. for relative paths in current dir)
            os.makedirs(parent_dir, exist_ok=True)

        video_input = ffmpeg.input(f'smptehdbars=size=320x240:duration={duration}:rate=30', format='lavfi') # Using smptehdbars source
        audio_input = ffmpeg.input(f'sine=frequency=440:duration={duration}', format='lavfi')
        (
            ffmpeg
            .output(video_input, audio_input, video_path, vcodec='libx264', acodec='aac', strict='experimental', video_bitrate='100k', audio_bitrate='64k', shortest=None) # rate=30 for video
            .run(cmd=['ffmpeg', '-nostdin'], overwrite_output=False, capture_stdout=True, capture_stderr=True)
        )
        print(f"Successfully created dummy video: {video_path}")
        return True
    except ffmpeg.Error as e:
        print(f"Error creating dummy video with ffmpeg: {video_path}")
        print(f"FFmpeg stdout: {e.stdout.decode('utf8') if e.stdout else 'N/A'}")
        print(f"FFmpeg stderr: {e.stderr.decode('utf8') if e.stderr else 'N/A'}")
        print(f"Please ensure ffmpeg is installed and in your system PATH.")
        print(f"Alternatively, place a video file at '{video_path}' manually.")
        return False
    except Exception as e_gen:
        print(f"An unexpected error occurred during dummy video creation: {e_gen}")
        return False

def main():
    # Load environment variables from .env file
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY") # job_handler.process_job also loads this, but good for early check.

    if not openai_api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file (copy from .env.example) and add your OpenAI API key.")
        print("Transcription will fail without it.")
        # Allow to continue if user only wants to test segmentation with a dummy video.
        # process_job will handle the None API key for transcription.

    # --- Sample Job Definition ---
    sample_video_relative_path = "inputs/video1.mp4"
    sample_output_relative_dir = "outputs/video1_job_output"

    # Resolve to absolute paths for clarity, though relative paths should also work
    base_dir = os.getcwd() # Use getcwd() for current working directory.
    sample_video_abs_path = os.path.join(base_dir, sample_video_relative_path)
    sample_output_abs_dir = os.path.join(base_dir, sample_output_relative_dir)

    # Create the dummy video for the sample job if it doesn't exist
    if not create_dummy_video_if_not_exists(sample_video_abs_path, duration=25): # 25s video for segments
        # If dummy video creation failed and file doesn't exist, we can't proceed with this sample job.
        if not os.path.exists(sample_video_abs_path):
            print(f"Exiting: Cannot run sample job without video at {sample_video_abs_path}")
            return

    sample_job = {
        "video_path": sample_video_abs_path,
        "segments": [
            {"start": "00:00:03", "end": "00:00:08"},
            {"start": "00:00:12", "end": "00:00:18"}
        ],
        "output_dir": sample_output_abs_dir
    }

    print(f"--- Starting Sample Job ---")
    print(f"Job Details: {json.dumps(sample_job, indent=2)}")

    # Clean up previous output directory for this sample job to ensure fresh run
    if os.path.exists(sample_job["output_dir"]):
        print(f"Cleaning up previous output directory: {sample_job['output_dir']}")
        shutil.rmtree(sample_job["output_dir"])

    try:
        results = process_job(sample_job)
        print("\n--- Sample Job Results ---")
        # Pretty print the JSON results
        print(json.dumps(results, indent=4))

        if results.get("job_status_file") and os.path.exists(results["job_status_file"]):
            print(f"\nFull job summary written to: {results['job_status_file']}")

        print("\n--- End of Sample Job ---")

    except Exception as e:
        print(f"An error occurred during job processing in main.py: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
