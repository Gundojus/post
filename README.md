
---

# Local Testing Guide

Follow these steps to test the application locally:

---

## 1. Install ImageMagick
- Download and install ImageMagick from the official website: [ImageMagick Download Page](https://imagemagick.org/script/download.php)
- During installation, ensure you check the box to include "Legacy Utilities" if prompted.

---

## 2. Update `main.py`
- Open the `main.py` file in your preferred editor.
- Locate **Line 12** and update it as follows:
  ```python
  change_settings({"IMAGEMAGICK_BINARY": "C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})
  ```
  *(This assumes ImageMagick is installed in the default location. If installed elsewhere, update the path accordingly.)*

---

## 3. Start the Application
- Open **Command Prompt** or your terminal.
- Run the following command to start the application:
  ```bash
  uvicorn main:app --reload
  ```

---

## 4. Test the Application Using Postman
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

## 5. Send the Request
- After filling in the required fields, click the **Send** button in Postman.
- Check the response for success or errors.

---

### Notes
- Make sure all dependencies for the project are installed (`pip install -r requirements.txt`).
- Ensure the `ImageMagick` path provided in `main.py` is correct.

---
