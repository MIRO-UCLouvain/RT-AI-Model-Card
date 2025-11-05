"""Module for file preview functionality."""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

_PREVIEW_LANG_BY_EXT: dict[str, str] = {
    ".txt": "text",
    ".csv": "csv",
    ".json": "json",
    ".md": "markdown",
    ".py": "python",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
}
_PREVIEW_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif"}
_PREVIEW_OTHER_EXTS = set(_PREVIEW_LANG_BY_EXT) | {".pdf"}


def preview_file(file_path: str) -> bool | None:
    """
    Render a file preview in Streamlit based on file extension.

    Supported formats:

    - Images: ``.png``, ``.jpg``, ``.jpeg``, ``.gif``
    - PDF: rendered inline with ``<iframe>``
    - Text/code: ``.txt``, ``.csv``, ``.json``, ``.md``, ``.py``, ``.c``,
        ``.cpp``, ``.h``

    :param file_path: Filesystem path to the file.
    :type file_path: str
    :returns:
        ``True`` if file was previewed, ``False`` if extension not supported,
        ``None`` if an error occurred.
    :rtype: bool | None
    """
    try:
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix in _PREVIEW_IMAGE_EXTS:
            st.image(str(path), use_container_width=True)
            return True
        if suffix == ".pdf":
            with path.open("rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode("utf-8")
            html = (
                f'<iframe src="data:application/pdf;base64,{base64_pdf}" '
                'width="100%" height="500px"></iframe>'
            )
            st.markdown(html, unsafe_allow_html=True)
            return True
        if suffix in _PREVIEW_OTHER_EXTS:
            lang = _PREVIEW_LANG_BY_EXT.get(suffix, "text")
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                st.code(f.read(), language=lang)
            return True
    except (OSError, UnicodeDecodeError):
        # I/O or decoding issues (file missing, permission,
        # or read/decode errors)
        return None
    else:
        return False

