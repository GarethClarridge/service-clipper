import ffmpeg
import os
from typing import Optional # Removed Union as it's not used

def get_video_duration(video_path: str) -> Optional[float]:
    """
    Retrieves the duration of a video using ffmpeg-python.

    Args:
        video_path (str): The path to the video file.

    Returns:
        Optional[float]: The duration of the video in seconds, or None if an error occurs.
    """
    try:
        if not os.path.exists(video_path): # Added explicit check for file existence
            print(f"Error: Video file not found at {video_path}")
            return None
        probe = ffmpeg.probe(video_path)
        duration = float(probe['format']['duration'])
        return duration
    except ffmpeg.Error as e:
        print(f"Error probing video: {video_path}. FFmpeg error: {e.stderr.decode('utf8') if e.stderr else 'Unknown ffmpeg error'}")
        return None
    except Exception as e_gen:
        print(f"A non-ffmpeg error occurred while trying to get video duration for {video_path}: {e_gen}")
        return None


def extract_full_audio_from_video(video_path: str, output_audio_path: str) -> Optional[str]:
    """
    Extracts the entire audio from a video file to a specified path.
    The output format is WAV, 16kHz, mono, which is good for Whisper.

    Args:
        video_path (str): The path to the input video file.
        output_audio_path (str): The path to save the extracted audio (e.g., 'temp/audio.wav').

    Returns:
        Optional[str]: The path to the extracted audio file if successful, None otherwise.
    """
    if not os.path.exists(video_path): # Added explicit check
        print(f"Error: Video file not found at {video_path} for audio extraction.")
        return None

    output_dir = os.path.dirname(output_audio_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        (
            ffmpeg
            .input(video_path)
            .output(output_audio_path, acodec='pcm_s16le', ac=1, ar='16k')
            .run(cmd=['ffmpeg', '-nostdin'], overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
        print(f"Audio extracted successfully to {output_audio_path}")
        return output_audio_path
    except ffmpeg.Error as e:
        print(f"Error extracting full audio from video: {video_path}")
        print(f"FFmpeg stdout: {e.stdout.decode('utf8') if e.stdout else 'N/A'}")
        print(f"FFmpeg stderr: {e.stderr.decode('utf8') if e.stderr else 'N/A'}")
        return None
    except Exception as e_gen:
        print(f"A non-ffmpeg error occurred during full audio extraction for {video_path}: {e_gen}")
        return None

def extract_audio_segment(input_path: str, start_time: str, end_time: str, output_path: str) -> Optional[str]:
    """
    Extracts a specific segment from an audio or video file and saves it as MP3.

    Args:
        input_path (str): Path to the input audio or video file.
        start_time (str): Start timestamp (e.g., "00:01:15").
        end_time (str): End timestamp (e.g., "00:01:45").
        output_path (str): Path to save the extracted MP3 audio segment.

    Returns:
        Optional[str]: The path to the extracted audio segment if successful, None otherwise.
    """
    if not os.path.exists(input_path): # Added explicit check
        print(f"Error: Input file not found at {input_path} for audio segment extraction.")
        return None

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        (
            ffmpeg
            .input(input_path, ss=start_time, to=end_time)
            .output(output_path, acodec='mp3', audio_bitrate='192k')
            .run(cmd=['ffmpeg', '-nostdin'], overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
        print(f"Audio segment extracted successfully to {output_path}")
        return output_path
    except ffmpeg.Error as e:
        print(f"Error extracting audio segment from: {input_path}")
        print(f"Start: {start_time}, End: {end_time}, Output: {output_path}")
        print(f"FFmpeg stdout: {e.stdout.decode('utf8') if e.stdout else 'N/A'}")
        print(f"FFmpeg stderr: {e.stderr.decode('utf8') if e.stderr else 'N/A'}")
        return None
    except Exception as e_gen:
        print(f"A non-ffmpeg error occurred during audio segment extraction for {input_path}: {e_gen}")
        return None


def extract_video_segment(video_path: str, start_time: str, end_time: str, output_path: str) -> Optional[str]:
    """
    Extracts a specific segment from a video file and saves it as MP4.

    Args:
        video_path (str): Path to the input video file.
        start_time (str): Start timestamp (e.g., "00:01:15").
        end_time (str): End timestamp (e.g., "00:01:45").
        output_path (str): Path to save the extracted MP4 video segment.

    Returns:
        Optional[str]: The path to the extracted video segment if successful, None otherwise.
    """
    if not os.path.exists(video_path): # Added explicit check
        print(f"Error: Video file not found at {video_path} for video segment extraction.")
        return None

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        (
            ffmpeg
            .input(video_path, ss=start_time, to=end_time)
            .output(output_path, vcodec='libx264', acodec='aac', strict='experimental', video_bitrate='1000k', audio_bitrate='192k')
            .run(cmd=['ffmpeg', '-nostdin'], overwrite_output=True, capture_stdout=True, capture_stderr=True)
        )
        print(f"Video segment extracted successfully to {output_path}")
        return output_path
    except ffmpeg.Error as e:
        print(f"Error extracting video segment from: {video_path}")
        print(f"Start: {start_time}, End: {end_time}, Output: {output_path}")
        print(f"FFmpeg stdout: {e.stdout.decode('utf8') if e.stdout else 'N/A'}")
        print(f"FFmpeg stderr: {e.stderr.decode('utf8') if e.stderr else 'N/A'}")
        return None
    except Exception as e_gen:
        print(f"A non-ffmpeg error occurred during video segment extraction for {video_path}: {e_gen}")
        return None
