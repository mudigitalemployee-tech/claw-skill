---
name: transcript-skill
description: "Transcribe YouTube, Wistia, Vimeo, or any embedded video on a webpage, plus local video/audio files, using Whisper AI, then summarize. ALWAYS use this skill — across ALL channels including WhatsApp — whenever: (1) user shares ANY video URL (YouTube, Wistia, Vimeo, or a webpage with embedded video like mu-sigma.com pages), (2) user shares a video or audio file attachment, (3) user says ANY of: transcript, transcribe, transcription, get transcript, summarize this video, summarize video, what does this video say, youtube transcript, video summary, audio transcript, give me the transcript, what is in this video, tell me what this video says, listen to this, convert video to text, convert audio to text, what is being said, summarize this, can you summarize (when a URL or file is present). Even if the user says just a URL or attaches a file without instructions — if it is a video/audio, use this skill. Supports YouTube URLs, Wistia URLs, Vimeo URLs, any webpage with embedded video (extracts Wistia media ID from page HTML), local video files (mp4, mkv, avi, webm, mov), and audio files (mp3, wav, m4a, flac, ogg). Works across ALL sessions and ALL channels. Do NOT wait for the user to explicitly name this skill. NOT for: general knowledge questions, Mu Sigma topics, or Qdrant/RAG queries."
homepage: https://github.com/openai/whisper
metadata: { "openclaw": { "emoji": "🎙️", "requires": { "bins": ["python3", "ffmpeg"] } } }
---

# Transcript — Video/Audio Transcription & Summarization

> ⚠️ **MANDATORY DISCLOSURE:** At the very end of every response using this skill, append:
> `_I used the transcript-skill to get this for you._ 🛠️`
> This is non-negotiable — applies on ALL channels including WhatsApp.

Extract transcripts from YouTube videos or local video/audio files, then summarize the content.

## Flow

```
[1] INPUT → [2] EXTRACT AUDIO → [3] TRANSCRIBE → [4] SUMMARIZE → [5] DELIVER
```

---

## Phase 1: INPUT

Determine the source type:

- **YouTube URL** (`youtube.com`, `youtu.be`) → Use `yt-dlp` to download audio
- **Wistia URL** (`wistia.com`, `wistia.net`, or any page with embedded Wistia video) → See Wistia flow below
- **Vimeo URL** (`vimeo.com`) → Use `yt-dlp` directly
- **Any webpage URL** (e.g. `mu-sigma.com`, company websites, blog posts) → Detect embedded video and extract
- **Local video file** (mp4, mkv, avi, webm, mov) → Use `ffmpeg` to extract audio
- **Local audio file** (mp3, wav, m4a, flac, ogg) → Use directly

### Detect video title and validate:
```bash
yt-dlp --print title "<url>" 2>/dev/null || echo "FALLBACK_NEEDED"
```
If title is found, show it and ask: "Found: **[title]**. Proceed with transcription?"
If yt-dlp fails on a webpage URL → use the Wistia/embedded extraction fallback below.

---

## 🎬 Wistia Video Handling (MANDATORY for Wistia and embedded pages)

Wistia videos appear in two forms:
1. **Direct Wistia URL**: `https://home.wistia.com/medias/<id>` or `https://*.wistia.com/medias/<id>`
2. **Embedded on a webpage**: e.g. `https://www.mu-sigma.com/some-page/` — page HTML contains Wistia embed code

### Step A — Extract Wistia media ID from the page

If the URL is a webpage (not directly youtube/vimeo):
```bash
# Fetch the page HTML and extract Wistia media ID
PAGE_HTML=$(curl -s -L --max-time 30 "<url>")

# Extract Wistia ID — it appears in embed codes, JSON, or script tags as:
# wistia.com/medias/<id>, wistia_embed/<id>, hashedId":"<id>", E-v1.js embed
WISTIA_ID=$(echo "$PAGE_HTML" | grep -oP '(?:wistia\.com/medias/|wistia_embed/|hashedId["\s:]+["\s])[a-z0-9]{10}' | grep -oP '[a-z0-9]{10}' | head -1)

# Alternative grep patterns
if [ -z "$WISTIA_ID" ]; then
  WISTIA_ID=$(echo "$PAGE_HTML" | grep -oP 'medias/[a-z0-9]{10}' | grep -oP '[a-z0-9]{10}' | head -1)
fi

echo "Wistia ID: $WISTIA_ID"
```

### Step B — Build direct Wistia URL and download
```bash
# Use direct Wistia media URL (bypasses the host website — works even if host is slow/blocked)
yt-dlp -x --audio-format wav --audio-quality 0 \
  -o "/tmp/transcript_audio.%(ext)s" \
  "https://home.wistia.com/medias/$WISTIA_ID"
```

### Step C — Fallback if direct URL fails
```bash
# Try wistia: scheme directly
yt-dlp -x --audio-format wav --audio-quality 0 \
  -o "/tmp/transcript_audio.%(ext)s" \
  "wistia:$WISTIA_ID"
```

### Step D — If yt-dlp cannot access Wistia (network restriction)
Use the Wistia Data API to get the direct MP4 URL:
```bash
# Get media info from Wistia API (no auth needed for public videos)
MEDIA_JSON=$(curl -s "https://fast.wistia.net/oembed?url=https://home.wistia.com/medias/$WISTIA_ID")
echo "$MEDIA_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('title','Unknown'))"

# Get direct MP4 download URL via Wistia assets API
ASSET_JSON=$(curl -s "https://fast.wistia.net/embed/medias/$WISTIA_ID.json")
MP4_URL=$(echo "$ASSET_JSON" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assets = d.get('media', {}).get('assets', [])
# Prefer mp4-360p or iphone-360p for smaller download
for a in assets:
    if a.get('type') == 'iphone_video' or '360' in a.get('display_name',''):
        print(a['url']); break
else:
    # Fall back to first video asset
    for a in assets:
        if a.get('content_type','').startswith('video'):
            print(a['url']); break
")
echo "Direct MP4 URL: $MP4_URL"

# Download MP4 and extract audio
curl -L -o /tmp/wistia_video.mp4 "$MP4_URL"
ffmpeg -i /tmp/wistia_video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 /tmp/transcript_audio.wav -y
```

### When to use Wistia flow:
- URL contains `wistia.com` or `wistia.net`
- URL is any webpage and yt-dlp's generic extractor detects a Wistia embed
- yt-dlp output shows `[Wistia]` in its extraction log

---

## Phase 2: EXTRACT AUDIO

### YouTube / Vimeo / Direct Wistia URL
```bash
yt-dlp -x --audio-format wav --audio-quality 0 -o "/tmp/transcript_audio.%(ext)s" "<url>"
```

### Webpage with embedded video (Wistia or other)
Follow the Wistia flow above (Phase 1 Wistia section) to extract and download.

### Local video
```bash
ffmpeg -i "<video_path>" -vn -acodec pcm_s16le -ar 16000 -ac 1 /tmp/transcript_audio.wav -y
```

### Local audio
Convert to WAV 16kHz mono for best Whisper results:
```bash
ffmpeg -i "<audio_path>" -acodec pcm_s16le -ar 16000 -ac 1 /tmp/transcript_audio.wav -y
```

---

## Phase 3: TRANSCRIBE (Whisper)

### Install dependencies (first run only)
```bash
pip install openai-whisper
```

If `openai-whisper` fails or is too slow, fall back to `faster-whisper`:
```bash
pip install faster-whisper
```

### Run transcription

Use `scripts/transcribe.py` to transcribe:
```bash
python3 scripts/transcribe.py --input /tmp/transcript_audio.wav --output /tmp/transcript.txt --model base
```

Model selection guide:
- **tiny** → Fastest, lowest accuracy. Good for quick previews.
- **base** → Default. Good balance of speed and accuracy.
- **small** → Better accuracy, slower.
- **medium** → High accuracy, requires more RAM.
- **large** → Best accuracy, slowest. Use only if user requests high quality.

Ask user preference only if transcription quality matters: "Which quality level? (fast/default/high)"
- fast → tiny
- default → base
- high → small or medium

Show progress: "🎙️ Transcribing audio... (this may take a few minutes)"

After transcription, show:
- Word count
- Estimated duration
- First 200 characters as preview

---

## Phase 4: SUMMARIZE

After transcription, read the full transcript text and use OpenClaw's own AI model to summarize it. Do NOT use any external summarization tool or library — just read the transcript and generate the summary yourself as the agent.

Generate a summary with these sections:

1. **Executive Summary** — 2-3 sentence overview
2. **Key Points** — Bullet list of main topics/arguments (5-8 bullets)
3. **Detailed Summary** — Paragraph-form summary covering the full content
4. **Notable Quotes** — Any memorable or important quotes (if applicable)

Present the summary to the user. Ask: "Want me to save the full transcript and summary?"

---

## Phase 5: DELIVER

Save outputs to the workspace:
```
~/workspace/transcripts/
├── <video-title>_transcript.txt    (full transcript)
├── <video-title>_summary.md        (formatted summary)
```

After saving, ask:
"Transcript and summary saved! Would you like to:
1. **Push to GitHub** — I'll create a repo and push
2. **Keep local** — All done
3. **Refine** — Adjust the summary or re-transcribe with higher quality"

### If push to GitHub:
```bash
cd ~/workspace/transcripts/
git init
git add .
git commit -m "Add transcript: <video-title>"
gh repo create transcript-<slug> --private --source=. --push
```

Send the repo link to user.

---

## Dependency Check

Before starting, verify required tools:
```bash
which yt-dlp || echo "MISSING: yt-dlp (pip install yt-dlp)"
which ffmpeg || echo "MISSING: ffmpeg (sudo apt install ffmpeg)"
python3 -c "import whisper" 2>/dev/null || echo "MISSING: openai-whisper (pip install openai-whisper)"
```

If any are missing, install them automatically and inform the user.

---

## Error Handling

- **yt-dlp fails on YouTube** → Check URL validity, try updating yt-dlp (`pip install -U yt-dlp`)
- **yt-dlp fails on a webpage URL** → Extract Wistia ID from HTML manually, use direct Wistia URL or Wistia API fallback
- **Wistia ID not found in page HTML** → Try fetching page with `curl -L` (follow redirects), check for `hashedId` or `medias/` in script tags
- **Wistia direct URL fails** → Use `wistia:<id>` scheme, then fall back to Wistia assets API + direct MP4 download
- **Network DNS failure (sandbox)** → Use `curl` to fetch page HTML and extract direct MP4 asset URLs from Wistia API (`fast.wistia.net/embed/medias/<id>.json`)
- **Age-restricted video** → Inform user, suggest downloading manually
- **ffmpeg fails** → Check file format, verify ffmpeg installation
- **Whisper OOM** → Fall back to smaller model (medium → small → base → tiny)
- **Long video (>2h)** → Warn user about processing time, suggest chunking
- **Private Wistia video** → Inform user the video requires authentication; ask them to download and share the file directly
