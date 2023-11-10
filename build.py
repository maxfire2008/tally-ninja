import pathlib
import subprocess
import shutil
import os
import uuid
import bs4


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


def main():
    os.chdir(pathlib.Path(__file__).parent.absolute())

    pathlib.Path("build/staging_main").mkdir(parents=True, exist_ok=True)

    shutil.copy("src/raceml.py", "build/staging_main/raceml.py")

    shutil.copy("src/editor.py", "build/staging_main/editor.py")
    new_launcher("src/editor.py", "build/staging_main/editor.exe", python_path="pyw")

    pathlib.Path("build/staging_pythonembedded").mkdir(parents=True, exist_ok=True)

    new_launcher(
        "src/editor.py",
        "build/staging_pythonembedded/editor.exe",
        python_path="./pythonembedded/pythonw.exe",
    )

    shutil.copy("LICENSE.md", "build/License.rtf")

    # open sportscorer.wxs and read the XML
    with open("sportscorer.wxs", "r") as f:
        soup = bs4.BeautifulSoup(f.read(), "xml")

    os.chdir((pathlib.Path(__file__).parent / "build").absolute())

    subprocess.run(
        ["wix", "extension", "add", "WixToolset.UI.wixext"],
        check=True,
    )

    # set the version number
    soup.find("Wix").find("Package")["UpgradeCode"] = str(uuid.uuid4())

    # write the XML back to sportscorer.wxs
    with open("sportscorer.wxs", "w") as f:
        f.write(str(soup))

    subprocess.run(
        [
            "wix",
            "build",
            "-ext",
            "WixToolset.UI.wixext",
            "-bindvariable",
            "WixUILicenseRtf=License.rtf",
            "-arch",
            "x64",
            "-out",
            "sportscorer-0.0.0-64.msi",
            "sportscorer.wxs",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
