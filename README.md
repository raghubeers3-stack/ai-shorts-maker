# AI Shorts Maker — Streamlit Cloud deployment

## Deploy to Streamlit Community Cloud

1. Sign in to GitHub and create a new repository named `ai-shorts-maker`.
2. Upload **all files inside this folder** to the repository root:
   - `app.py`
   - `requirements.txt`
   - `packages.txt`
   - `.gitignore`
   - `README.md`
3. Open https://share.streamlit.io/ and sign in with GitHub.
4. Select **Create app**, choose your `ai-shorts-maker` repository, branch `main`, and main file `app.py`.
5. Select **Deploy**. Streamlit will build the app and provide its public URL.

## What this starter currently does
- Accepts uploaded video files you own or are authorized to edit.
- Detects embedded audio tracks and lets you select one.
- Uses Faster-Whisper to transcribe speech and identify speech-rich time windows.
- Exports vertical 9:16 MP4 clips for download.

## Important limitations
- This is a starter MVP, not a production-ready service.
- YouTube URL downloading is not implemented. Do not bypass YouTube access controls, DRM, or platform restrictions. Upload a source file you are authorized to use.
- Language selection is available only for audio tracks embedded in the uploaded file.
- Subtitle burning, semantic viral-moment ranking, and AI dubbing are not yet implemented.
- Public hosting has resource, execution-time, and storage limits. Large videos may fail or exceed available resources. For production, use dedicated background workers and object storage.
- Review copyright, music, privacy, and other rights before publishing generated clips.
