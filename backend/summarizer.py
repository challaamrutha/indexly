import re


def clean_text(text: str) -> str:
    return " ".join(
        text.strip().split()
    )


def split_sentences(text: str):
    text = clean_text(text)

    if not text:
        return []

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def summarize_text(
    text: str,
    max_sentences: int = 2,
    max_characters: int = 240,
) -> str:
    """
    Creates a concise extractive summary from indexed content.

    This deliberately uses the actual transcript/OCR text.
    It does not invent information that isn't present.
    """

    text = clean_text(text)

    if not text:
        return "No summary available."

    sentences = split_sentences(text)

    if not sentences:
        return text[:max_characters].rstrip()

    if len(sentences) <= max_sentences:
        summary = " ".join(sentences)
    else:
        summary = " ".join(
            sentences[:max_sentences]
        )

    if len(summary) > max_characters:
        summary = (
            summary[:max_characters]
            .rsplit(" ", 1)[0]
            + "..."
        )

    return summary


def summarize_result(
    result_type: str,
    description: str,
) -> str:
    description = clean_text(
        description
    )

    if not description:
        if result_type == "visual":
            return "Visual match found at this moment."

        return "Relevant spoken content found at this moment."

    summary = summarize_text(
        description
    )

    if result_type == "visual":
        return f"Visual match: {summary}"

    return summary
