from queue import Queue

from logging import exception
import logging
from multiprocessing.pool import ThreadPool
import os
from random import Random, randint, random
import subprocess
import sys
from this import s
from threading import Thread, Timer, activeCount
import threading
import time
from pathlib import Path
from concurrent.futures import (
    ALL_COMPLETED,
    Future,
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    process,
)
import concurrent.futures
import multiprocessing


class ConversionResult:
    PositionInQueue = 0
    imgPath: Path = None


class conversionSettings:
    imgPath: Path = None
    format: str = None
    cmd: str = None

    def __init__(self, imgPath, format, settings=None) -> None:
        self.imgPath = imgPath
        self.format = format
        self.cmd = settings


class imageConverter(object):
    def __init__(self):
        self.magickEXE = "C:\Program Files\ImageMagick\magick.exe"
        self.ddsArgs = "-define dds:compression{dxt5}"
        self.defaultargs = "-quality 100"
        self.imageCount = 0
        self.imgformat = "tga"
        self.active_conversions = set()
        self.finished_conversions: list[conversionSettings] = []
        self.failed_conversions: list[conversionSettings] = []
        self.conversionQueue: list[conversionSettings] = []
        self.messageQ = Queue()
        self.printqueue = Queue()
        self.supported_formats = [
            "AI",
            "APNG",
            "ART",
            "ARW",
            "AVI",
            "AVIF",
            "AVS",
            "BPG",
            "BMP",
            "BMP2",
            "BMP3",
            "BRF",
            "CALS",
            "CIN",
            "CIP",
            "CMYK",
            "CMYKA",
            "CR2",
            "CRW",
            "CUBE",
            "CUR",
            "CUT",
            "DCM",
            "DCR",
            "DCX",
            "DDS",
            "DEBUG",
            "DIB",
            "DJVU",
            "DNG",
            "DOT",
            "DPX",
            "EMF",
            "EPDF",
            "EPI",
            "EPS",
            "EPS2",
            "EPS3",
            "EPSF",
            "EPSI",
            "EPT",
            "EXR",
            "FARBFELD",
            "FAX",
            "FITS",
            "FL32",
            "FLIF",
            "FPX",
            "FTXT",
            "GIF",
            "GPLT",
            "GRAY",
            "GRAYA",
            "HDR",
            "HDR",
            "HEIC",
            "HPGL",
            "HRZ",
            "HTML",
            "ICO",
            "INFO",
            "ISOBRL",
            "ISOBRL6",
            "JBIG",
            "JNG",
            "JP2",
            "JPT",
            "J2C",
            "J2K",
            "JPEG",
            "JPG",
            "JXR",
            "JSON",
            "JXL",
            "KERNEL",
            "MAN",
            "MAT",
            "MIFF",
            "MONO",
            "MNG",
            "M2V",
            "MPEG",
            "MPC",
            "MPR",
            "MRW",
            "MSL",
            "MTV",
            "MVG",
            "NEF",
            "ORF",
            "ORA",
            "OTB",
            "P7",
            "PALM",
            "PAM",
            "CLIPBOARD",
            "PBM",
            "PCD",
            "PCDS",
            "PCL",
            "PCX",
            "PDB",
            "PDF",
            "PEF",
            "PES",
            "PFA",
            "PFB",
            "PFM",
            "PGM",
            "PHM",
            "PICON",
            "PICT",
            "PIX",
            "PNG",
            "PNG8",
            "PNG00",
            "PNG24",
            "PNG32",
            "PNG48",
            "PNG64",
            "PNM",
            "POCKETMOD",
            "PPM",
            "PS",
            "PS2",
            "PS3",
            "PSB",
            "PSD",
            "PTIF",
            "PWP",
            "QOI",
            "RAD",
            "RAF",
            "RAW",
            "RGB",
            "RGB565",
            "RGBA",
            "RGF",
            "RLA",
            "RLE",
            "SCT",
            "SFW",
            "SGI",
            "SHTML",
            "SID",
            "MrSID",
            "SPARSE-COLOR",
            "STRIMG",
            "SUN",
            "SVG",
            "TEXT",
            "TGA",
            "TIFF",
            "TIF",
            "TIM",
            "TTF",
            "TXT",
            "UBRL",
            "UBRL6",
            "UIL",
            "UYVY",
            "VICAR",
            "VIDEO",
            "VIFF",
            "WBMP",
            "WDP",
            "WEBP",
            "WMF",
            "WPG",
            "X",
            "XBM",
            "XCF",
            "XPM",
            "XWD",
            "X3F",
            "YAML",
            "YCbCr",
            "YCbCrA",
            "YUV",
        ]

    def findFilesInArgs(self, args: list[str]) -> list[Path] | None:
        files = []
        for _, arg in enumerate(args):
            path = Path(arg).resolve()
            if path.is_file() and path.exists():
                files.append(path)
        return files

    def findFoldersInArgs(self, args: list[str]):
        folders = []
        for _, arg in enumerate(args):
            path = Path(arg).resolve()
            if path.is_dir() and path.exists():
                folders.append(path)
        return folders

    def findOuputDirInArgs(self, args: list[str]):
        for index, arg in enumerate(args):
            if "-o" in arg and index + 1 < len(args):
                folder = args[index + 1]
                folder = Path(folder).resolve()
                if folder.exists():
                    return folder
        return None

    def findTargetFormatInArgs(self, args):
        format = ""
        for index, arg in enumerate(args):
            if arg == "-f" and index + 1 < len(args):
                format = args[index + 1]
                if str(format).startswith("."):
                    format = format[1:]
                if str.upper(format) in self.supported_formats:
                    return format
            elif arg.startswith("-f") and index + 1 < len(args):
                format = arg[2:].strip()
                if str(format).startswith("."):
                    format = format[1:]
                if str.upper(format) in self.supported_formats:
                    return format
        return None

    def checkIsFileSupported(self, file: Path):
        return file.suffix.replace(".", "").upper() in self.supported_formats

    def main(self):
        args = sys.argv[1:]

        argdirs = self.findFoldersInArgs(args)
        argfiles = self.findFilesInArgs(args)
        outdir = self.findOuputDirInArgs(args)
        imgformat = self.findTargetFormatInArgs(args)

        # collect all files in arg-passed directories
        for dir in argdirs:
            for root, _, files in os.walk(dir):
                for f in files:
                    argfiles.append(Path(root).joinpath(f))

        # make argfiles list unique
        argfiles = dict.fromkeys(argfiles, None)
        argfiles = list(argfiles.keys())

        # generate conversion commands
        for file in argfiles:
            if not self.checkIsFileSupported(file):
                continue

            if outdir is None:
                outfile = file.resolve().with_suffix(f".{imgformat.lower()}")
            else:
                outfile = outdir / file.name.with_suffix(f".{imgformat.lower()}")

            convertCMD = f'"{self.magickEXE}" "{file}" {self.ddsArgs} {self.defaultargs} "{outfile}"'
            self.conversionQueue.append(conversionSettings(file, imgformat, convertCMD))
            self.imageCount += 1

        # set terminal window siz
        os.system("mode con: cols=70 lines=40")
        print(
            "               Image converter by SmittyWerben\n"
            + "==============================================================\n"
            + f"converting {self.imageCount} images to {imgformat}\n"
            + "______________________________________________________________\n"
        )

        if imgformat == None:
            print(
                'ERROR: Invalid or unsupported file format. \nAdd an argument for the desired format anywhere in the command\n  example: "-f tga"'
            )
            return

        if not Path("C:\Program Files\ImageMagick\magick.exe").exists():
            print(
                'ERROR: ImageMagick not found.\nMake sure you have it installed in:\n\t"C:\Program Files\ImageMagick\magick.exe"'
            )
            return

        with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            futures = []
            for setting in self.conversionQueue:
                futures.append(executor.submit(self.convert, setting))

            progress = self.getProgress()
            while progress < 100:
                progress = self.getProgress()
                self.printUpdate()
                time.sleep(0.2)
            print("\n")

        self.printResults()
        self.continueIn(5)

    def printUpdate(self):
        active = len(self.active_conversions)
        failed = len(self.failed_conversions)
        finished = len(self.finished_conversions)

        if not self.printqueue.empty():
            print(self.printqueue.get_nowait())

        progress = self.getProgress()
        print(
            f"active: {active} - finished: {finished} - failed: {failed} -- ",
            f"Progress: {progress}% ...",
            end="\r",
        )

    def printResults(self):
        print("==============================================================")
        print("Conversion finished!\nResults:")

        print("🆗 Finished: " + str(len(self.finished_conversions)))
        print("⚠️  Failed:", end="")
        if len(self.failed_conversions) == 0:
            print("0")
        else:
            print("\n")
            for _, f in enumerate(self.failed_conversions):
                print(f.imgPath.name)

    def continueIn(self, sleeptime=5):
        print(f"Contiuing in {sleeptime} seconds ...")
        time.sleep(sleeptime)

    def registerConversion(self, settings: conversionSettings):
        self.active_conversions.add(settings)

    def getProgress(self):
        completed = len(self.finished_conversions) + len(self.failed_conversions)
        total = self.imageCount
        x = round((completed / (total)) * 100)
        return x

    def reportConversion(self, status: str, settings: conversionSettings):
        if status == "FAILED":
            self.failed_conversions.append(settings)
        elif status == "FINISHED":
            self.finished_conversions.append(settings)
        try:
            self.active_conversions.remove(settings)
            self.conversionQueue.remove(settings)
        except:
            pass

    def convert(self, settings: conversionSettings):
        try:
            # register Conversion Task
            self.registerConversion(settings)

            # execute conversion
            subprocess.check_call(
                settings.cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except:
            # report failed Conversion
            self.reportConversion("FAILED", settings)

        # callback Completion
        self.reportConversion("FINISHED", settings)


if __name__ == "__main__":
    try:
        imageConverter().main()
    except Exception as e:
        print(e)
        time.sleep(5)
