import os
import openai
from dotenv import load_dotenv
from utils.ffmpeg_utils import extract_full_audio_from_video

def transcribe_video(video_path: str, temp_audio_path: str = "outputs/temp_audio/temp_for_whisper.wav") -> str | None:
    """
    Transcribes the audio from a video file using OpenAI Whisper.

    Args:
        video_path (str): The path to the video file.
        temp_audio_path (str): The path to store the temporary extracted audio file.
                               Defaults to "outputs/temp_audio/temp_for_whisper.wav".

    Returns:
        str | None: The transcript text if successful, None otherwise.
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file (copy from .env.example) and add your API key.")
        return None

    openai.api_key = api_key

    print(f"Extracting audio from {video_path} to {temp_audio_path} for transcription...")
    # Ensure the directory for the temp_audio_path exists
    temp_audio_dir = os.path.dirname(temp_audio_path)
    if temp_audio_dir: # Check if temp_audio_dir is not an empty string
        os.makedirs(temp_audio_dir, exist_ok=True)

    extracted_audio_file_path = extract_full_audio_from_video(video_path, temp_audio_path)

    if not extracted_audio_file_path or not os.path.exists(extracted_audio_file_path):
        print(f"Failed to extract audio from {video_path}. Transcription aborted.")
        return None

    transcript_text = None
    try:
        print(f"Transcribing audio file: {extracted_audio_file_path} using OpenAI Whisper...")
        with open(extracted_audio_file_path, "rb") as audio_file:
            response = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        # The response object structure for v1.x openai library is response.text
        transcript_text = response.text
        print("Transcription successful.")
    except openai.APIError as e:
        print(f"OpenAI API error during transcription: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response Body: {e.response.text}")
        elif hasattr(e, 'message'):
             print(f"Error Message: {e.message}")
    except Exception as e:
        print(f"An unexpected error occurred during transcription: {e}")
    finally:
        # Clean up the temporary audio file
        if os.path.exists(extracted_audio_file_path):
            try:
                os.remove(extracted_audio_file_path)
                print(f"Temporary audio file {extracted_audio_file_path} removed.")
                # Attempt to remove the directory if it's empty
                # temp_audio_dir is already defined above
                if os.path.exists(temp_audio_dir) and not os.listdir(temp_audio_dir):
                    os.rmdir(temp_audio_dir)
                    print(f"Temporary audio directory {temp_audio_dir} removed as it was empty.")
            except OSError as e_os:
                print(f"Error removing temporary file/directory {extracted_audio_file_path}: {e_os}")

    return transcript_text
