from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from moviepy.editor import (
    ImageClip,
    CompositeVideoClip,
    concatenate_videoclips,
    AudioFileClip,
)
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
import yt_dlp
from pathlib import Path
import tempfile
import uuid
import subprocess

from moviepy.config import change_settings
# Update ImageMagick path for Windows
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

app = FastAPI()

# Paths to static assets
WATERMARK_PATH = "./watermark.png"
BACKDROP_PATH = "./backdrop.png"
OUTPUT_DIR = "./output"  # Directory to persist generated videos

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


def delete_all_videos(directory_path: str):
    """
    Check the specified directory and delete all video files.
    
    Parameters:
        directory_path (str): Path to the directory to scan for video files.
        
    Returns:
        list: A list of deleted video file paths.
    """
    # Common video file extensions
    video_extensions = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mpeg", ".mpg"}
    deleted_files = []

    # Check if the directory exists
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"The directory {directory_path} does not exist.")

    # Walk through all files in the directory
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            _, ext = os.path.splitext(file_path)
            
            # Check if the file has a video extension
            if ext.lower() in video_extensions:
                try:
                    os.remove(file_path)  # Delete the file
                    deleted_files.append(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")


def download_youtube_audio(youtube_link: str, output_path: str) -> str:
    """Download YouTube audio using yt_dlp and save it to the specified path."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_link])
    return output_path


def create_text_image(text: str, font_path: str, fontsize: int, color: str, size: tuple) -> Image.Image:
    """Create an image with the given text."""
    img = Image.new('RGBA', size, (255, 255, 255, 0))  # Transparent background
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, fontsize)
    except IOError:
        font = ImageFont.load_default()
    text_size = draw.textsize(text, font=font)
    position = ((size[0] - text_size[0]) / 2, (size[1] - text_size[1]) / 2 - 250)
    draw.text(position, text, font=font, fill=color)
    return img


@app.post("/generate-video/")
async def generate_video(
    image: UploadFile = File(...),
    text: str = Form(...),
    youtube_link: str = Form(...),
    audio_offset_mm: int = Form(...),
    audio_offset_ss: int = Form(...),
):
    try:
        # Verify ffmpeg availability
        try:
            subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            raise EnvironmentError("ffmpeg is not installed or not accessible. Please install it and add it to your PATH.")

        delete_all_videos(".")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Save uploaded image to temporary file
            img_path = temp_path / "input_image.png"
            img = Image.open(BytesIO(await image.read())).convert("RGBA")
            img.save(img_path)

            # Open image and watermark
            base_img = Image.open(img_path).convert("RGBA")
            base_img = base_img.resize((1080, 1920), Image.ANTIALIAS)
            watermark = Image.open(WATERMARK_PATH).convert("RGBA")
            # Resize watermark to maintain aspect ratio with height=214
            watermark_ratio = 214 / watermark.height
            watermark_size = (int(watermark.width * watermark_ratio), 214)
            watermark = watermark.resize(watermark_size, Image.ANTIALIAS)
            # Paste watermark onto base image
            base_img.paste(watermark, (0, 0), watermark)
            # Save the composed image
            composed_img_path = temp_path / "composed_image.png"
            base_img.save(composed_img_path)

            # Create text image
            text_img_path = temp_path / "text_image.png"
            text_img = create_text_image(
                text=text,
                font_path="./Benedict.otf",
                fontsize=150,
                color="black",
                size=(1080, 1920)
            )
            text_img.save(text_img_path)

            # Define audio template with %(ext)s
            audio_template = temp_path / "youtube_audio.%(ext)s"

            # Download YouTube audio to temporary file
            download_youtube_audio(youtube_link, str(audio_template))

            # Define the expected mp3 path
            audio_path = temp_path / "youtube_audio.mp3"

            if not audio_path.exists():
                raise FileNotFoundError(f"Expected audio file not found: {audio_path}.")

            # Calculate audio offset in seconds
            offset_seconds = audio_offset_mm * 60 + audio_offset_ss

            with AudioFileClip(str(audio_path)) as audio_clip_full:
                audio_clip = audio_clip_full.subclip(offset_seconds, offset_seconds + 14).volumex(0.5)

                page_duration = 7
                transition_duration = 2
                balance = 2

                # Ensure image fills 1080x1920 frame
                composed_img_clip = (
                    ImageClip(str(composed_img_path))
                    .resize(height=1920)
                    .resize(width=1080)
                    .set_duration(page_duration + balance)
                    .set_fps(1)
                )

                # Text image clip
                text_image_clip = (
                    ImageClip(str(text_img_path))
                    .set_duration(page_duration - balance)
                    .set_fps(24)
                )

                # Backdrop clip
                backdrop_clip = (
                    ImageClip(BACKDROP_PATH)
                    .resize(height=1920)
                    .resize(width=1080)
                    .set_duration(page_duration - balance)
                    .set_fps(1)
                )

                second_page = CompositeVideoClip([backdrop_clip, text_image_clip], size=(1080, 1920)).set_fps(24)

                first_page = composed_img_clip.crossfadeout(transition_duration / 2)
                second_page = second_page.crossfadein(transition_duration / 2)

                final_video = concatenate_videoclips([first_page, second_page], method="compose")

                final_video = final_video.set_audio(audio_clip)

                output_filename = f"final_video_{uuid.uuid4().hex}.mp4"
                output_path = Path(OUTPUT_DIR) / output_filename

                with final_video:
                    final_video.write_videofile(
                        str(output_path),
                        fps=24,
                        codec="libx264",
                        audio_codec="aac",
                        preset="ultrafast",
                        ffmpeg_params=["-crf", "28"],
                        bitrate="500k",
                        threads=os.cpu_count(),
                    )

            if not output_path.exists():
                raise FileNotFoundError(f"Video file not found: {output_path}")

            return FileResponse(
                path=str(output_path),
                media_type="video/mp4",
                filename=output_path.name,
            )

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
