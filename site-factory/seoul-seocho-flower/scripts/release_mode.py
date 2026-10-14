"""Read the same fail-closed source release contract used by Astro."""
import json
import subprocess
from pathlib import Path


def release_mode(root):
    root = Path(root).resolve()
    try:
        result = subprocess.run(
            ['node', str(Path(__file__).with_suffix('.mjs')), str(root)],
            check=True, capture_output=True, text=True, encoding='utf-8', timeout=30,
        )
    except subprocess.CalledProcessError as error:
        raise AssertionError('Release contract rejected: ' + error.stderr[:1500]) from None
    return json.loads(result.stdout)
