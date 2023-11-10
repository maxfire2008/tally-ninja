import pathlib
import subprocess
import shutil
import os
import uuid
import createmsi


def new_launcher(python_file, output_exe):
    code = (
        """#include <stdio.h>
#include <stdlib.h>

int main()
{
    char *args[] = {"pyw", \""""
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

    # create the staging_main directory
    pathlib.Path("build/staging_main").mkdir(parents=True, exist_ok=True)

    shutil.copy("src/raceml.py", "build/staging_main/raceml.py")

    shutil.copy("src/editor.py", "build/staging_main/editor.py")
    new_launcher("src/editor.py", "build/staging_main/editor.exe")

    shutil.copy("LICENSE.md", "build/LICENSE.rtf")

    os.chdir((pathlib.Path(__file__).parent / "build").absolute())

    subprocess.run(
        ["wix", "extension", "add", "WixToolset.UI.wixext"],
        check=True,
    )

    p = createmsi.PackageGenerator(
        {
            "product_guid": "6ab45328-44f0-4af1-8bd7-9c58e9c42d6e",
            "upgrade_guid": str(uuid.uuid4()),
            "version": "0.0.0",
            "product_name": "Sport Scorer",
            "manufacturer": "Max Burgess",
            "name": "Sport Scorer",
            "name_base": "sportscorer",
            "comments": "A comment describing the program",
            "installdir": "SportScorer",
            "license_file": "License.rtf",
            "parts": [
                {
                    "id": "SportScorer",
                    "title": "Sport Scorer",
                    "description": "Sport Scorer Suite",
                    "absent": "disallow",
                    "staged_dir": "staging_main",
                }
            ],
        }
    )
    p.generate_files()
    p.build_package()


if __name__ == "__main__":
    main()
