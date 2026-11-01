"""Run original tests; model link metadata only when Windows denies link creation.

This tests publisher rejection logic, not OS symlink traversal. Original tests and
publisher code stay unchanged. Linux CI must still exercise physical symlinks.
"""
import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

parser = argparse.ArgumentParser()
parser.add_argument('region', choices=['dongjak', 'geumcheon'])
parser.add_argument('source', type=Path)
args = parser.parse_args()
os.environ['DIRECT_SOURCE_ROOT'] = str(args.source.resolve())
root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('publisher_tests', root / f'scripts/direct-seoul-{args.region}/test_publish.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
links = set()
fallbacks = []
original_link, original_islink, original_unlink = Path.symlink_to, Path.is_symlink, Path.unlink


def symlink(path, target, target_is_directory=False):
    try:
        return original_link(path, target, target_is_directory)
    except OSError as error:
        if os.name != 'nt' or getattr(error, 'winerror', None) != 1314:
            raise
        # Keep a real filesystem entry for rglob, but inject its rejected type.
        if target_is_directory:
            path.mkdir()
        else:
            shutil.copyfile(target, path)
        links.add(path.absolute())
        fallbacks.append(str(path.name))


def unlink(path, missing_ok=False):
    if path.absolute() in links:
        links.remove(path.absolute())
        if path.is_dir():
            return path.rmdir()
    return original_unlink(path, missing_ok=missing_ok)


with patch.object(Path, 'symlink_to', symlink), \
     patch.object(Path, 'is_symlink', lambda path: path.absolute() in links or original_islink(path)), \
     patch.object(Path, 'unlink', unlink):
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
print(f'Windows link metadata fixtures: {len(fallbacks)}; physical-link traversal is not verified by fallback.')
raise SystemExit(not result.wasSuccessful())
