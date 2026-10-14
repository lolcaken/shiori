"""Build the yt-dlp -o filename template (date - title [lang].ext)."""


def video_filename_template(sub_tag: str) -> str:
    tag = f" [{sub_tag}]" if sub_tag else ""
    return (
        "%(upload_date>%Y-%m-%d,release_date>%Y-%m-%d|unknown)s"
        f" - %(title)s{tag}.%(ext)s"
    )
