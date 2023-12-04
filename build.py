import pathlib
import subprocess
import shutil
import os
import uuid
import zipfile
import io
import sys
import bs4
import requests


def new_launcher(python_file, output_exe, python_path="pyw"):
    code = (
        """#include <stdio.h>
#include <stdlib.h>

int main()
{
    char *args[] = {\""""
        + python_path
        + """\", \""""
        + python_file
        + """\", NULL};
    execvp(args[0], args);
    return 0;
}"""
    )

    # pipe the code directly into gcc
    gcc = subprocess.Popen(
        ["gcc", "-x", "c", "-o", output_exe, "-"], stdin=subprocess.PIPE
    )

    # write the code to gcc
    gcc.stdin.write(code.encode("utf-8"))

    # close the pipe
    gcc.stdin.close()

    # wait for gcc to finish
    gcc.wait()


def download_embedded_python(output_dir):
    if len(sys.argv) > 1 and sys.argv[1] == "skip_download":
        return
    if not isinstance(output_dir, pathlib.Path):
        output_dir = pathlib.Path(output_dir)

    # delete output_dir if it exists
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # download the python embedded zip
    response = requests.get(
        "https://www.python.org/ftp/python/3.11.6/python-3.11.6-embed-amd64.zip",
        stream=True,
    )

    # extract the zip
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        zip_file.extractall(output_dir)


def main():
    os.chdir(pathlib.Path(__file__).parent.absolute())

    pathlib.Path("build/staging_main").mkdir(parents=True, exist_ok=True)

    shutil.copy("src/raceml.py", "build/staging_main/raceml.py")
    shutil.copy("src/editor.py", "build/staging_main/editor.py")
    new_launcher(
        "editor.py",
        "build/staging_main/editor.exe",
        python_path="./python_embedded/pythonw.exe",
    )

    shutil.copy("requirements.txt", "build/requirements.txt")

    os.chdir("build")

    download_embedded_python("staging_main/python_embedded")

    # install packages from requirements.txt to staging_main/python_embedded/Lib/site-packages
    subprocess.run(
        [
            "py",
            "-m",
            "pip",
            "install",
            "-r",
            "requirements.txt",
            "--target",
            "staging_main/python_embedded/Lib/site-packages",
        ],
        check=True,
    )

    print("Done! Make sure to create the NSIS installer!")


if __name__ == "__main__":
    main()
