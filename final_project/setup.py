#!/usr/bin/env python3

from pathlib import Path, PurePath, PosixPath
from shutil import copyfile

"""
This script copies the necessary .g files to the 
"""

src = Path("../scenarios")
dst = PosixPath('~/git/robotics-course/scenarios').expanduser()
src_files = list(src.glob('*'))
for file_name in src_files:
    dst_ = dst / file_name.name
    copyfile(str(file_name), str(dst_))
