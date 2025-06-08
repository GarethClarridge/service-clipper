import os
import shutil
import json
from datetime import datetime
from typing import Optional, Dict, List, Any # Added import

from transcriber.transcribe import transcribe_video
from segmenter.segment import export_segments

INPUTS_DIR = "inputs"

def process_job(job_details: Dict[str, Any]) -> Dict[str, Any]: # Changed type hint for job_details and return
    """
    Processes a video job, including transcription and segment extraction.

    Args:
        job_details (Dict[str, Any]): A dictionary containing job parameters:
            - "video_path" (str): Path to the input video file.
            - "segments" (List[Dict[str, str]]): List of segments to extract.
            - "output_dir" (str): Directory to save all outputs for this job.

    Returns:
        Dict[str, Any]: A dictionary containing the results:
            - "transcript_content" (Optional[str]): Raw transcript text.
            - "transcript_file" (Optional[str]): Path to the saved transcript file.
            - "exported_audio_segments" (List[str]): List of paths to exported audio files.
            - "exported_video_segments" (List[str]): List of paths to exported video files.
            - "video_path_processed" (str): Path of the processed video.
            - "job_output_directory" (str): Path of the output directory for the job.
            - "job_status_file" (Optional[str]): Path to a JSON file containing all results.
            - "error" (Optional[str]): Error message if any.
    """
    video_path: Optional[str] = job_details.get("video_path")
    segments_to_export: List[Dict[str, str]] = job_details.get("segments", [])
    output_dir: Optional[str] = job_details.get("output_dir")

    results_template: Dict[str, Any] = {
        "transcript_content": None,
        "transcript_file": None,
        "exported_audio_segments": [],
        "exported_video_segments": [],
        "video_path_processed": video_path,
        "job_output_directory": output_dir, # Will be updated if defaulted
        "job_status_file": None,
        "error": None
    }

    if not video_path or not os.path.exists(video_path):
        msg = f"Error: Video path '{video_path}' not provided or video does not exist."
        print(msg)
        results_template["error"] = msg
        # Ensure video_path_processed is set even if video_path is None initially
        results_template["video_path_processed"] = video_path if video_path else "Not provided"
        return results_template

    if not output_dir:
        video_basename = os.path.basename(video_path) # video_path is confirmed to exist here
        output_dir = os.path.join("outputs", os.path.splitext(video_basename)[0] + "_job_output")
        print(f"Warning: 'output_dir' not specified. Using default: {output_dir}")

    results_template["job_output_directory"] = output_dir # Set actual output_dir used
    os.makedirs(output_dir, exist_ok=True)

    # --- 1. Transcription ---
    temp_audio_dir = os.path.join(output_dir, "temp_audio")
    os.makedirs(temp_audio_dir, exist_ok=True)
    video_name_without_ext = os.path.splitext(os.path.basename(video_path))[0]
    temp_audio_for_transcription = os.path.join(temp_audio_dir, f"{video_name_without_ext}_whisper_input.wav")

    print(f"Starting transcription for {video_path} (temp audio: {temp_audio_for_transcription})...")
    transcript_text_content = transcribe_video(video_path, temp_audio_path=temp_audio_for_transcription)
    results_template["transcript_content"] = transcript_text_content

    if transcript_text_content is not None:
        transcript_file_path = os.path.join(output_dir, "transcript.txt")
        try:
            with open(transcript_file_path, 'w', encoding='utf-8') as f:
                f.write(transcript_text_content)
            print(f"Transcript saved to: {transcript_file_path}")
            results_template["transcript_file"] = transcript_file_path
        except IOError as e:
            print(f"Error saving transcript to {transcript_file_path}: {e}")
            # transcript_file_path remains None in results_template
            if results_template["error"] is None: # Prioritize more specific errors
                 results_template["error"] = f"Failed to save transcript: {e}"
    else:
        print(f"Transcription failed for {video_path}.")
        if results_template["error"] is None:
             results_template["error"] = "Transcription failed."


    # --- 2. Segment Export ---
    if segments_to_export:
        segments_output_dir = os.path.join(output_dir, "segments")
        os.makedirs(segments_output_dir, exist_ok=True)
        print(f"Exporting segments from {video_path} to {segments_output_dir}...")

        segment_results = export_segments(
            video_path=video_path,
            segments=segments_to_export,
            output_dir=segments_output_dir
        )
        results_template["exported_audio_segments"] = segment_results.get("audio_segments", [])
        results_template["exported_video_segments"] = segment_results.get("video_segments", [])
        print(f"Segment export complete. Audio: {len(results_template['exported_audio_segments'])}, Video: {len(results_template['exported_video_segments'])} segments.")
    else:
        print("No segments specified in the job. Skipping segment export.")

    # Consolidate error messages if multiple steps failed but no primary error was set
    if transcript_text_content is None and not results_template["exported_audio_segments"] and not results_template["exported_video_segments"] and results_template["error"] is None :
        if not segments_to_export :
            results_template["error"] = "Transcription failed and no segments were requested for export."
        else:
            results_template["error"] = "Transcription failed and segment export produced no files."

    job_status_filename = os.path.join(output_dir, "job_summary.json")
    try:
        with open(job_status_filename, 'w', encoding='utf-8') as f_json:
            json.dump(results_template, f_json, indent=4)
        print(f"Job summary saved to: {job_status_filename}")
        results_template["job_status_file"] = job_status_filename
    except IOError as e:
        print(f"Error saving job summary JSON to {job_status_filename}: {e}")
        if results_template["error"] is None:
            results_template["error"] = f"Failed to save job summary: {e}"
        # job_status_file remains None in results_template

    return results_template

_OLD_OUTPUTS_DIR = "outputs_old_workflow"
_OLD_PROCESSED_DIR = os.path.join(_OLD_OUTPUTS_DIR, "processed")
_OLD_TRANSCRIPTS_DIR = os.path.join(_OLD_OUTPUTS_DIR, "transcripts")
_OLD_AUDIO_CHUNKS_DIR = os.path.join(_OLD_OUTPUTS_DIR, "audio_chunks")

os.makedirs(_OLD_PROCESSED_DIR, exist_ok=True)
os.makedirs(_OLD_TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(_OLD_AUDIO_CHUNKS_DIR, exist_ok=True)

def process_video_file_old(video_path: str, openai_api_key: str, segment_length: int = 600) -> Optional[str]:
    print(f"Processing video (OLD WORKFLOW): {video_path}")
    video_filename = os.path.basename(video_path)
    video_name_without_ext = os.path.splitext(video_filename)[0]

    temp_audio_for_transcription = os.path.join(_OLD_AUDIO_CHUNKS_DIR, f"{video_name_without_ext}_temp_full_audio.wav")
    os.makedirs(os.path.dirname(temp_audio_for_transcription), exist_ok=True)

    transcript_text = transcribe_video(video_path, temp_audio_path=temp_audio_for_transcription)

    if transcript_text is None:
        print(f"Transcription failed for {video_path} (OLD WORKFLOW).")
        return None

    final_transcript_path = os.path.join(_OLD_TRANSCRIPTS_DIR, f"{video_name_without_ext}_transcript.txt")
    try:
        os.makedirs(_OLD_TRANSCRIPTS_DIR, exist_ok=True)
        with open(final_transcript_path, 'w', encoding='utf-8') as f: f.write(transcript_text)
    except IOError as e:
        print(f"Error saving final transcript {final_transcript_path} (OLD WORKFLOW): {e}")
        return None

    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        processed_video_path = os.path.join(_OLD_PROCESSED_DIR, f"{video_name_without_ext}_{timestamp}{os.path.splitext(video_filename)[1]}")
        os.makedirs(_OLD_PROCESSED_DIR, exist_ok=True)
        shutil.move(video_path, processed_video_path)
    except Exception as e:
        print(f"Error moving processed video {video_path} (OLD WORKFLOW): {e}")
    return final_transcript_path

def process_all_videos_in_input_dir_old(openai_api_key: str, segment_length: int = 600) -> None:
    print(f"Starting to process all videos in: {INPUTS_DIR} (OLD WORKFLOW)")
    processed_count = 0; failed_count = 0

    # Check if INPUTS_DIR exists and is readable
    if not os.path.isdir(INPUTS_DIR):
        print(f"Error: Input directory '{INPUTS_DIR}' not found or not a directory (OLD WORKFLOW).")
        return

    video_files_found = False
    for filename in os.listdir(INPUTS_DIR):
        file_path = os.path.join(INPUTS_DIR, filename)
        if os.path.isfile(file_path) and filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            video_files_found = True
            print(f"Found video (OLD WORKFLOW): {filename}")
            if process_video_file_old(file_path, openai_api_key, segment_length):
                processed_count += 1
            else:
                failed_count += 1
        # else: print(f"Skipping: {filename} (OLD WORKFLOW)") # Reduce noise
    print(f"\nProcessing summary (OLD WORKFLOW): Success: {processed_count}, Failed: {failed_count}") # Added newline for clarity
    if not video_files_found: # Check if any video files were iterated over
        print("No video files found in input directory for OLD WORKFLOW.")
