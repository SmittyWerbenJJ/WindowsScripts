# # find archive files in folder and move them to a folder
# # with the same name as the archive

# from doctest import OutputChecker
# from pathlib import Path
# import subprocess
# import os
# import time
# import shutil


import sys
import argparse
import py7zr
import rarfile
import shutil
from pyunpack import Archive
from pathlib import Path
RARSUFFIX = ".rar"
SEVENZIPSUFFIX = ".7z"
ARCHIVESUFFIXES = [".zip", RARSUFFIX, SEVENZIPSUFFIX]
# cwd = os.getcwd()


def getUnpackDirectory(archivePath: Path):
    return archivePath.parent.joinpath(archivePath.stem).joinpath(archivePath.stem)


def extractArchive(archivePath: Path):
    """extract archives with pyunpack
    https://github.com/ponty/pyunpack
    Args:
        zipname (Path): the zp to extract
        output_dir (Path): the output directory
    """
    unpackDirectory = getUnpackDirectory(archivePath)
    unpackDirectory.mkdir(parents=True, exist_ok=True)
    Archive(archivePath).extractall(unpackDirectory, auto_create_dir=True)


def MoveArchive(archivePath: str):
    """Moves a file to a directory

    Args:
        inPath (str): the file to move
        outPath (str): the direcotry to MOVE TO

    Raises:
        ValueError: _description_
    """
    unpackDirectory = getUnpackDirectory(archivePath).parent
    shutil.move(archivePath, unpackDirectory)


def countArchiveFiles(path: Path):
    archiveFiles = []
    for item in path.iterdir():
        if item.is_file():
            if item.suffix.lower() in ARCHIVESUFFIXES:
                archiveFiles.append(item)
    return archiveFiles


def extractAndMove(archivePaths: Path):
    for path in archivePaths:
        print("  %s ..." % path.name)
        extractArchive(path)
        MoveArchive(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="the folder or file that will be processed", type=Path, nargs="+")
    args = parser.parse_args()

    for pathString in args.path:

        path = Path(pathString)

        if not path.is_dir() or path.exists() == False:
            print("Selected Path is not a folder or does not exist")
            break

        # counting archive files in path
        archivePaths = countArchiveFiles(path)
        if len(archivePaths) == 0:
            print("No Archives to Extract. Quitting")
            break

        print("Extracting %s Files ..." % len(archivePaths))
        extractAndMove(archivePaths)
    print("DONE")
