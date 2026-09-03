from faster_whisper import WhisperModel


# Load Whisper once when the backend imports this file.
# "tiny" is being used for the first working test because it is
# already downloaded on your Mac.
model = WhisperModel(
    "tiny",
    device="cpu",
    compute_type="int8",
)


def transcribe_video(video_path: str):
    """
    Transcribe a video and return real timestamps from Whisper.
    """

    segments, info = model.transcribe(
        video_path,
        beam_size=5,
        vad_filter=True,
        word_timestamps=True,
    )

    transcript = []

    for segment in segments:
        words = []

        if segment.words:
            for word in segment.words:
                words.append(
                    {
                        "word": word.word.strip(),
                        "start": word.start,
                        "end": word.end,
                    }
                )

        transcript.append(
            {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "words": words,
            }
        )

    return {
        "language": info.language,
        "duration": info.duration,
        "segments": transcript,
    }
