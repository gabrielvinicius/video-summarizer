# transcription/infrastructure/ffmpeg_adapter.py
import subprocess
import tempfile


class FFmpegConverter:
    def extract_audio(self, video_path: str) -> str:
        with tempfile.NamedTemporaryFile(suffix=".mp3") as tmp:
            command = [
                "ffmpeg",
                "-i", video_path,
                "-vn", "-acodec", "libmp3lame",
                tmp.name
            ]
            subprocess.run(command, check=True)
            return tmp.name
