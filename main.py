"""
MCP server for fetching YouTube subtitles using yt-dlp.
"""

import os
import glob
from mcp.server.fastmcp import FastMCP
import yt_dlp

# Create an MCP server
mcp = FastMCP("YouTube Subtitles", json_response=True)

@mcp.tool()
def get_subtitles(url: str, lang: str = "en") -> str:
    """
    Get subtitles for a YouTube video.
    
    Args:
        url: The URL of the YouTube video.
        lang: The language code for the subtitles (default: "en").
    
    Returns:
        The subtitle content in VTT format, or an error message.
    """
    # unique prefix to avoid collisions if running concurrently (though mcp is usually sequential here)
    # but better safe. We'll use the video id as filename.
    
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [lang],
        'outtmpl': '/tmp/%(id)s',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id')
            
            # Construct expected filename pattern
            # yt-dlp names it as {outtmpl}.{lang}.{ext}
            # e.g. /tmp/VIDEO_ID.en.vtt
            
            # We look for any file matching the pattern in case extension varies
            pattern = f"/tmp/{video_id}.{lang}.*"
            files = glob.glob(pattern)
            
            if not files:
                return f"No subtitles found for language '{lang}'."
            
            # Pick the first one (usually vtt)
            subtitle_file = files[0]
            
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean up
            for f in files:
                try:
                    os.remove(f)
                except OSError:
                    pass
            
            return content

    except Exception as e:
        return f"Error fetching subtitles: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")