import os
from utils.ffmpeg_utils import extract_audio_segment, extract_video_segment
from typing import List, Dict # Added import

def export_segments(video_path: str, segments: List[Dict[str, str]], output_dir: str) -> Dict[str, List[str]]:
    """
    Exports specified audio and video segments from a video file.

    Args:
        video_path (str): Path to the input video file.
        segments (List[Dict[str, str]]): A list of segment dictionaries, each with "start" and "end" timestamps.
                               Example: [{"start": "00:00:10", "end": "00:00:20"}, ...]
        output_dir (str): The directory to save the exported segment files.

    Returns:
        Dict[str, List[str]]: A dictionary with keys "audio_segments" and "video_segments",
                              containing lists of paths to the exported files.
                              Returns empty lists if no segments are processed or if errors occur.
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return {"audio_segments": [], "video_segments": []}

    os.makedirs(output_dir, exist_ok=True)

    exported_audio_files: List[str] = [] # Added type hint
    exported_video_files: List[str] = [] # Added type hint

    base_filename = os.path.splitext(os.path.basename(video_path))[0]

    for i, seg_info in enumerate(segments):
        start_time = seg_info.get("start")
        end_time = seg_info.get("end")

        if not start_time or not end_time:
            print(f"Warning: Segment {i+1} is missing start or end time. Skipping.")
            continue

        # Sanitize start and end times for use in filenames
        safe_start_time = start_time.replace(":", "-")
        safe_end_time = end_time.replace(":", "-")

        segment_filename_base = f"{base_filename}_segment_{i+1}_{safe_start_time}_{safe_end_time}"

        # Define output paths for audio and video segments
        audio_output_path = os.path.join(output_dir, f"{segment_filename_base}_audio.mp3")
        video_output_path = os.path.join(output_dir, f"{segment_filename_base}_video.mp4")

        print(f"Exporting segment {i+1}: {start_time} - {end_time}")

        # Extract audio segment
        audio_file = extract_audio_segment(video_path, start_time, end_time, audio_output_path)
        if audio_file and os.path.exists(audio_file):
            exported_audio_files.append(audio_file)
            print(f"Successfully exported audio segment to {audio_file}")
        else:
            print(f"Failed to export audio segment {i+1} for {video_path}")

        # Extract video segment
        video_file = extract_video_segment(video_path, start_time, end_time, video_output_path)
        if video_file and os.path.exists(video_file):
            exported_video_files.append(video_file)
            print(f"Successfully exported video segment to {video_file}")
        else:
            print(f"Failed to export video segment {i+1} for {video_path}")

    return {"audio_segments": exported_audio_files, "video_segments": exported_video_files}
