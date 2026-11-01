import os, json, subprocess, tempfile, shutil
from pathlib import Path
import streamlit as st
from faster_whisper import WhisperModel

st.set_page_config(page_title="AI Shorts Maker", page_icon="🎬", layout="wide")
st.title("🎬 AI Shorts Maker")
st.caption("Create vertical Shorts from videos you own or are authorized to edit.")

def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-2500:])
    return p.stdout

def probe(path):
    data = json.loads(run(["ffprobe","-v","quiet","-print_format","json","-show_streams",str(path)]))
    return [s for s in data.get("streams",[]) if s.get("codec_type")=="audio"]

def get_duration(path):
    data = json.loads(run(["ffprobe","-v","quiet","-print_format","json","-show_format",str(path)]))
    return float(data["format"]["duration"])

def make_short(src, dst, start, end, audio_index, subtitles=None):
    # audio_index is the absolute stream index reported by ffprobe
    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    cmd = ["ffmpeg","-y","-ss",str(start),"-i",str(src),"-t",str(end-start),
           "-map","0:v:0","-map",f"0:{audio_index}","-vf",vf,
           "-c:v","libx264","-preset","veryfast","-crf","23",
           "-c:a","aac","-b:a","192k","-movflags","+faststart",str(dst)]
    run(cmd)

def transcribe(path, language):
    model = WhisperModel(os.getenv("WHISPER_MODEL","base"), device="cpu", compute_type="int8")
    kwargs = {}
    if language != "Auto detect":
        kwargs["language"] = {"Hindi":"hi","English":"en","Tamil":"ta","Telugu":"te",
                              "Bengali":"bn","Marathi":"mr","Malayalam":"ml","Kannada":"kn"}.get(language)
    segments, info = model.transcribe(str(path), vad_filter=True, **kwargs)
    return list(segments), info

def choose_segments(segments, duration, clip_len):
    # MVP heuristic: select non-overlapping transcript windows with substantial speech.
    windows, step = [], max(clip_len, 35)
    t = 0.0
    while t < duration:
        end = min(t + clip_len, duration)
        if end - t >= 12:
            speech = sum(max(0, min(end,s.end)-max(t,s.start)) for s in segments)
            if speech >= min(8, (end-t)*0.25):
                windows.append((t,end))
        t += step
    return windows[:12]

st.info("YouTube URL importing is intentionally not enabled in this starter build. Upload a video file you own or have permission to use. This avoids bypassing platform download restrictions.")
uploaded = st.file_uploader("Upload source video", type=["mp4","mov","mkv","webm","m4v"])
if uploaded:
    work = Path(tempfile.mkdtemp(prefix="shorts_"))
    source = work / uploaded.name
    source.write_bytes(uploaded.getbuffer())
    try:
        audios = probe(source)
        if not audios:
            st.error("No audio tracks found in this video.")
            st.stop()
        st.subheader("1. Choose source audio language")
        labels = []
        for i, a in enumerate(audios):
            tags = a.get("tags",{})
            lang = tags.get("language","und")
            title = tags.get("title",f"Audio track {i+1}")
            labels.append(f"{lang.upper()} — {title} (track {i+1})")
        choice = st.selectbox("Available audio tracks", range(len(audios)), format_func=lambda i: labels[i])
        audio_stream_index = audios[choice]["index"]
        st.subheader("2. Shorts settings")
        col1,col2,col3 = st.columns(3)
        with col1:
            clip_len = st.selectbox("Clip length", [30,45,60,90], index=1)
        with col2:
            caption_lang = st.selectbox("Caption language", ["Same as audio","Hindi","English","Tamil","Telugu","Bengali","Marathi","Malayalam","Kannada","Auto detect"])
        with col3:
            count = st.slider("Maximum Shorts",1,10,5)
        if st.button("✨ Find moments and create Shorts", type="primary"):
            with st.spinner("Transcribing selected audio and finding speech-rich moments..."):
                try:
                    # Extract selected audio stream for speech recognition.
                    audio_path = work / "selected_audio.wav"
                    run(["ffmpeg","-y","-i",str(source),"-map",f"0:{audio_stream_index}",
                         "-ac","1","-ar","16000",str(audio_path)])
                    lang = caption_lang if caption_lang not in ("Same as audio","Auto detect") else "Auto detect"
                    segments, info = transcribe(audio_path, lang)
                    windows = choose_segments(segments, get_duration(source), clip_len)[:count]
                    if not windows:
                        st.warning("No speech-rich sections were detected. Try a longer clip length or another audio track.")
                    else:
                        outdir = Path("output")
                        outdir.mkdir(exist_ok=True)
                        for n,(start,end) in enumerate(windows,1):
                            dst = outdir / f"short_{n:02d}.mp4"
                            make_short(source,dst,start,end,audio_stream_index)
                            st.success(f"Created Short {n}: {start:.1f}s–{end:.1f}s")
                            st.video(str(dst))
                            st.download_button(f"Download Short {n}", dst.read_bytes(),
                                                file_name=dst.name, mime="video/mp4", key=f"dl{n}")
                        st.caption("MVP note: clips are selected using speech-density heuristics. Review each clip before publishing.")
                except Exception as e:
                    st.error(f"Processing failed: {e}")
                    st.caption("Make sure FFmpeg is installed and the selected audio stream is readable.")
    except Exception as e:
        st.error(f"Could not inspect this video: {e}")
    finally:
        # Keep the uploaded file for the duration of this Streamlit session.
        pass
else:
    st.markdown("### Included in this starter MVP")
    st.markdown("- Detects audio tracks embedded in an uploaded video and lets you choose one.\n- Uses the selected track for speech recognition and clip selection.\n- Creates 9:16 MP4 clips and offers individual downloads.\n- Supports Hindi/English and several Indic transcription languages through local Whisper.")
