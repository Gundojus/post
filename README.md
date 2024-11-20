---

# Local Testing Guide

Follow these steps to test the application locally:

---

## 1. Install ImageMagick
- Download and install **ImageMagick** from the official website: [ImageMagick Download Page](https://imagemagick.org/script/download.php)
- During installation:
  - Ensure you check the box to include **"Legacy Utilities"** if prompted.

---

## 2. Install FFmpeg
- Download **FFmpeg** for Windows from the official website: [FFmpeg Download Page](https://ffmpeg.org/download.html)
- Follow these steps:
  1. Extract the downloaded archive (e.g., `ffmpeg-release-essentials.zip`) to a folder (e.g., `C:\ffmpeg`).
  2. Add the `bin` directory to your system's **PATH** environment variable:
     - Navigate to **System Properties** > **Advanced** > **Environment Variables**.
     - Under **System Variables**, find and edit the `Path` variable.
     - Add the path to FFmpeg's `bin` directory (e.g., `C:\ffmpeg\bin`).
  3. Verify the installation:
     - Open a Command Prompt and run:
       ```bash
       ffmpeg -version
       ```
     - You should see version details of FFmpeg.

---

## 3. Update `main.py`
- Open the `main.py` file in your preferred editor.
- Locate **Line 12** and update it as follows:
  ```python
  change_settings({"IMAGEMAGICK_BINARY": "C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})
  ```
  *(This assumes ImageMagick is installed in the default location. If installed elsewhere, update the path accordingly.)*

---

## 4. Start the Application
- Open **Command Prompt** or your terminal.
- Run the following command to start the application:
  ```bash
  uvicorn main:app --reload
  ```

---

## 5. Test the Application Using Postman
- Open **Postman** and create a new **HTTP Request**:
  - **Method**: POST
  - **URL**: `http://127.0.0.1:8000/generate-video/`

- In the request:
  - Go to the **Body** tab and select **form-data**.

### Add the Following Keys:
1. **Text Fields** (as `text` type):
   - `text`: Enter a string value (required).
   - `youtube_link`: Enter a valid YouTube URL (required).
   - `audio_offset_mm`: Enter an integer value for minutes (required).
   - `audio_offset_ss`: Enter an integer value for seconds (required).

2. **File Field**:
   - `image`: Upload an image file (required).

---

## 6. Send the Request
- After filling in the required fields, click the **Send** button in Postman.
- Check the response for success or errors.

---

### Notes
- Ensure all dependencies for the project are installed:
  ```bash
  pip install -r requirements.txt
  ```
- Verify that:
  - The `ImageMagick` path provided in `main.py` is correct.
  - FFmpeg is installed and accessible via the system's PATH.

---
