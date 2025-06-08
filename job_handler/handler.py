import os
import shutil
import json # For potentially writing out job results as JSON
from datetime import datetime

# Assuming utils.ffmpeg_utils is primarily used by transcriber and segmenter now.
# from utils.ffmpeg_utils import get_video_duration

from transcriber.transcribe import transcribe_video
from segmenter.segment import export_segments # Import the new segmenter function

# Define fixed paths for general inputs (if needed by other functions)
# However, process_job will use output_dir from job_details.
INPUTS_DIR = "inputs"
# OUTPUTS_DIR = "outputs" # This might be superseded by job_details["output_dir"]
# PROCESSED_DIR = os.path.join(OUTPUTS_DIR, "processed") # Specific to old workflow
# TRANSCRIPTS_DIR = os.path.join(OUTPUTS_DIR, "transcripts") # Specific to old workflow
# AUDIO_CHUNKS_DIR = os.path.join(OUTPUTS_DIR, "audio_chunks") # Specific to old workflow

# Ensure general directories exist if other functions still use them
# os.makedirs(PROCESSED_DIR, exist_ok=True)
# os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
# os.makedirs(AUDIO_CHUNKS_DIR, exist_ok=True)

def process_job(job_details: dict) -> dict:
    """
    Processes a video job, including transcription and segment extraction.

    Args:
        job_details (dict): A dictionary containing job parameters:
            - "video_path" (str): Path to the input video file.
            - "segments" (list[dict]): List of segments to extract,
                                       each {"start": "HH:MM:SS", "end": "HH:MM:SS"}.
            - "output_dir" (str): Directory to save all outputs for this job.

    Returns:
        dict: A dictionary containing the results:
            - "transcript_file" (str|None): Path to the saved transcript file, or None if failed.
            - "exported_audio_segments" (list[str]): List of paths to exported audio segment files.
            - "exported_video_segments" (list[str]): List of paths to exported video segment files.
            - "job_status_file" (str|None): Path to a JSON file containing all results.
    """
    video_path = job_details.get("video_path")
    segments_to_export = job_details.get("segments", [])
    output_dir = job_details.get("output_dir")

    if not video_path or not os.path.exists(video_path):
        print(f"Error: Video path '{video_path}' not provided or video does not exist.")
        return {
            "transcript_content": None,
            "transcript_file": None,
            "exported_audio_segments": [],
            "exported_video_segments": [],
            "job_status_file": None,
            "error": f"Video path '{video_path}' not provided or video does not exist."
        }

    if not output_dir:
        print("Error: 'output_dir' not specified in job details.")
        # Defaulting to a generic output, though job should always specify this
        video_basename = os.path.basename(video_path) if video_path else "unknown_video"
        output_dir = os.path.join("outputs", os.path.splitext(video_basename)[0] + "_job_output")
        print(f"Using default output directory: {output_dir}")

    # Ensure the main output directory for the job exists
    os.makedirs(output_dir, exist_ok=True)

    # --- 1. Transcription ---
    transcript_file_path = None
    transcript_text_content = None # Store the actual transcript text

    # Define a path for the temporary audio file that transcribe_video will use
    # Place it inside the job's output directory to keep things organized
    temp_audio_dir = os.path.join(output_dir, "temp_audio")
    os.makedirs(temp_audio_dir, exist_ok=True)
    video_name_without_ext = os.path.splitext(os.path.basename(video_path))[0]
    temp_audio_for_transcription = os.path.join(temp_audio_dir, f"{video_name_without_ext}_whisper_input.wav")

    print(f"Starting transcription for {video_path} (temp audio: {temp_audio_for_transcription})...")
    transcript_text_content = transcribe_video(video_path, temp_audio_path=temp_audio_for_transcription)

    if transcript_text_content is not None:
        transcript_file_path = os.path.join(output_dir, "transcript.txt")
        try:
            with open(transcript_file_path, 'w', encoding='utf-8') as f:
                f.write(transcript_text_content)
            print(f"Transcript saved to: {transcript_file_path}")
        except IOError as e:
            print(f"Error saving transcript to {transcript_file_path}: {e}")
            transcript_file_path = None # Mark as None if saving failed
    else:
        print(f"Transcription failed for {video_path}.")

    # --- 2. Segment Export ---
    exported_audio_files = []
    exported_video_files = []

    if segments_to_export:
        segments_output_dir = os.path.join(output_dir, "segments")
        os.makedirs(segments_output_dir, exist_ok=True)
        print(f"Exporting segments from {video_path} to {segments_output_dir}...")

        segment_results = export_segments(
            video_path=video_path,
            segments=segments_to_export,
            output_dir=segments_output_dir
        )
        exported_audio_files = segment_results.get("audio_segments", [])
        exported_video_files = segment_results.get("video_segments", [])
        print(f"Segment export complete. Audio: {len(exported_audio_files)}, Video: {len(exported_video_files)} segments.")
    else:
        print("No segments specified in the job. Skipping segment export.")

    # --- 3. Consolidate Results ---
    final_results = {
        "transcript_content": transcript_text_content, # Including raw transcript
        "transcript_file": transcript_file_path,
        "exported_audio_segments": exported_audio_files,
        "exported_video_segments": exported_video_files,
        "video_path_processed": video_path,
        "job_output_directory": output_dir,
        "error": None # Initialize error as None
    }
    if transcript_text_content is None and not segments_to_export : # if both failed or weren't requested
        final_results["error"] = "Transcription failed and no segments were requested for export."
    elif transcript_text_content is None:
        final_results["error"] = "Transcription failed."

    # Optionally, save the full job results to a JSON file in the output directory
    job_status_filename = os.path.join(output_dir, "job_summary.json")
    try:
        with open(job_status_filename, 'w', encoding='utf-8') as f_json:
            json.dump(final_results, f_json, indent=4)
        print(f"Job summary saved to: {job_status_filename}")
        final_results["job_status_file"] = job_status_filename
    except IOError as e:
        print(f"Error saving job summary JSON to {job_status_filename}: {e}")
        final_results["job_status_file"] = None

    return final_results


# The old functions (process_video_file, process_all_videos_in_input_dir) are kept below.
# They represent a different workflow (batch processing from a fixed 'inputs' folder without segment definitions).
# They can be deprecated or removed if main.py switches entirely to the job_details based workflow.

# Define fixed paths for the old workflow
_OLD_OUTPUTS_DIR = "outputs_old_workflow" # Renamed to avoid conflict
_OLD_PROCESSED_DIR = os.path.join(_OLD_OUTPUTS_DIR, "processed")
_OLD_TRANSCRIPTS_DIR = os.path.join(_OLD_OUTPUTS_DIR, "transcripts")
_OLD_AUDIO_CHUNKS_DIR = os.path.join(_OLD_OUTPUTS_DIR, "audio_chunks")

# Ensure these directories are created when the module is loaded if old functions are kept.
os.makedirs(_OLD_PROCESSED_DIR, exist_ok=True)
os.makedirs(_OLD_TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(_OLD_AUDIO_CHUNKS_DIR, exist_ok=True)

def process_video_file_old(video_path, openai_api_key, segment_length=600): # segment_length is unused
    print(f"Processing video (OLD WORKFLOW): {video_path}")
    video_filename = os.path.basename(video_path)
    video_name_without_ext = os.path.splitext(video_filename)[0]

    temp_audio_for_transcription = os.path.join(_OLD_AUDIO_CHUNKS_DIR, f"{video_name_without_ext}_temp_full_audio.wav")

    # Ensure the directory for temp_audio_for_transcription exists
    os.makedirs(os.path.dirname(temp_audio_for_transcription), exist_ok=True)

    transcript_text = transcribe_video(video_path, temp_audio_path=temp_audio_for_transcription)

    if transcript_text is None:
        print(f"Transcription failed for {video_path} (OLD WORKFLOW).")
        return None

    final_transcript_path = os.path.join(_OLD_TRANSCRIPTS_DIR, f"{video_name_without_ext}_transcript.txt")
    try:
        # Ensure _OLD_TRANSCRIPTS_DIR exists
        os.makedirs(_OLD_TRANSCRIPTS_DIR, exist_ok=True)
        with open(final_transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript_text)
    except IOError as e:
        print(f"Error saving final transcript {final_transcript_path} (OLD WORKFLOW): {e}")
        return None

    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        processed_video_path = os.path.join(_OLD_PROCESSED_DIR, f"{video_name_without_ext}_{timestamp}{os.path.splitext(video_filename)[1]}")
        # Ensure _OLD_PROCESSED_DIR exists
        os.makedirs(_OLD_PROCESSED_DIR, exist_ok=True)
        shutil.move(video_path, processed_video_path)
    except Exception as e:
        print(f"Error moving processed video {video_path} (OLD WORKFLOW): {e}")

    return final_transcript_path

def process_all_videos_in_input_dir_old(openai_api_key, segment_length=600): # segment_length is unused
    print(f"Starting to process all videos in: {INPUTS_DIR} (OLD WORKFLOW)")
    processed_count = 0
    failed_count = 0

    for filename in os.listdir(INPUTS_DIR):
        file_path = os.path.join(INPUTS_DIR, filename)
        if os.path.isfile(file_path):
            if filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')): # Basic video check
                print(f"Found video (OLD WORKFLOW): {filename}")
                transcript_path = process_video_file_old(file_path, openai_api_key, segment_length)
                if transcript_path:
                    print(f"Successfully processed {filename} (OLD WORKFLOW). Transcript: {transcript_path}")
                    processed_count += 1
                else:
                    print(f"Failed to process {filename} (OLD WORKFLOW)")
                    failed_count += 1
            else:
                print(f"Skipping non-video file: {filename} (OLD WORKFLOW)")
        else:
            print(f"Skipping directory: {filename} (OLD WORKFLOW)")

    print("\nProcessing summary (OLD WORKFLOW):")
    print(f"Successfully processed videos: {processed_count}")
    print(f"Failed to process videos: {failed_count}")

    if processed_count == 0 and failed_count == 0:
        print("No video files found in the input directory for OLD WORKFLOW.")
