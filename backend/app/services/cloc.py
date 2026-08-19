import json
import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)


def dir_parser(directories, temp_dir: str) -> list:
    """Convert absolute temp-dir paths to relative paths for portability."""
    final_dir = []
    for path in directories:
        if temp_dir in path:
            relative = os.path.relpath(path, temp_dir)
            final_dir.append(relative)
    return final_dir


def get_comment_to_code(url: str):
    """
    Clone *url* with depth 1 into a temp directory, run cloc, and return
    (SUM dict, relative file paths list) or None on any failure.
    """
    if not url:
        return None

    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "echo"

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", "--single-branch", url, temp_dir],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
                env=env,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception) as exc:
            logger.warning("git clone failed or timed out for %s: %s", url, exc)
            return None

        try:
            result = subprocess.run(
                ["cloc", temp_dir, "--json", "--by-file"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception) as exc:
            logger.warning("cloc failed or timed out for %s: %s", url, exc)
            return None

        try:
            data = json.loads(result.stdout)
            if not isinstance(data, dict):
                return None
            file_keys = {k for k in data if k not in ("header", "SUM")}
            file_list = dir_parser(file_keys, temp_dir)
            return data.get("SUM"), file_list
        except (json.JSONDecodeError, Exception):
            return None
