from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from moviepy.editor import VideoClip, ImageClip, CompositeVideoClip, TextClip, concatenate_videoclips, AudioFileClip
from PIL import Image
from io import BytesIO
import os
import yt_dlp
import tempfile
from pathlib import Path

from moviepy.config import change_settings
change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

app = FastAPI()

# Paths to static assets
WATERMARK_PATH = "./watermark.png"
BACKDROP_PATH = "./backdrop.png"


def download_youtube_audio(youtube_link: str, output_path: str) -> str:
    """Download YouTube audio using yt-dlp and save it to the specified path."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}
        ]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_link])
    return output_path


@app.post("/generate-video/")
async def generate_video(
    image: UploadFile = File(...),
    text: str = Form(...),
    youtube_link: str = Form(...),
    audio_offset_mm: int = Form(...),
    audio_offset_ss: int = Form(...)
):
    try:
        # Use a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Save uploaded image to temporary file
            img_path = temp_path / "input_image.png"
            img = Image.open(BytesIO(await image.read()))
            img.save(img_path)

            # Download YouTube audio to temporary file
            audio_filename = "youtube_audio.mp3"
            audio_path = temp_path / audio_filename
            download_youtube_audio(youtube_link, str(audio_path.with_suffix("")))

            # Apply audio offset and trim audio to 14 seconds
            offset_seconds = audio_offset_mm * 60 + audio_offset_ss
            audio_clip = AudioFileClip(str(audio_path)).subclip(offset_seconds, offset_seconds + 14).volumex(0.5)

            # Set duration variables
            page_duration = 7  # Duration for each page
            transition_duration = 2  # Duration of the transition
            balance = 2  # Balance adjustment for pages

            # Create the watermark and backdrop clips
            watermark = ImageClip(WATERMARK_PATH).set_position(("left", "top")).resize(height=214).set_duration(page_duration + balance)
            backdrop = ImageClip(BACKDROP_PATH).set_duration(page_duration - balance)

            # First Page: Show Image with Watermark
            img_clip = ImageClip(str(img_path)).set_duration(page_duration + balance).resize(height=1920)
            first_page = CompositeVideoClip([img_clip, watermark], size=(1080, 1920)).set_duration(page_duration + balance)

            # Second Page: Text over Backdrop
            text_clip = TextClip(
                text,
                fontsize=150,
                font="./Benedict.otf",
                color="black",
            ).set_position(("center", 647.2)).set_duration(page_duration - balance)  # Center horizontally
            second_page = CompositeVideoClip([backdrop, text_clip], size=(1080, 1920)).set_duration(page_duration - balance)

            # Add transitions between pages
            first_page = first_page.crossfadeout(transition_duration / 2)
            second_page = second_page.crossfadein(transition_duration / 2)

            # Concatenate clips with transitions
            final_video = concatenate_videoclips([first_page, second_page], method="compose")

            # Add audio to the final video
            final_video = final_video.set_audio(audio_clip)

            # Save video to temporary file
            output_path = temp_path / "final_video.mp4"
            final_video.write_videofile(
                str(output_path), fps=24, codec="libx264", audio_codec="aac", preset="ultrafast", threads=4
            )

            # Close the audio clip explicitly to release the file lock
            audio_clip.close()

            return FileResponse(str(output_path), media_type="video/mp4", filename="final_video.mp4")

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
