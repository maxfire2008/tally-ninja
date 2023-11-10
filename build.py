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
    new_launcher("src/editor.py", "build/staging_main/editor.exe", python_path="pyw")

    pathlib.Path("build/staging_pythonembedded").mkdir(parents=True, exist_ok=True)

    new_launcher(
        "src/editor.py",
        "build/staging_pythonembedded/editor.exe",
        python_path="./pythonembedded/pythonw.exe",
    )

    shutil.copy("LICENSE.md", "build/License.rtf")
    shutil.copy("requirements.txt", "build/requirements.txt")

    # open sportscorer.wxs and read the XML
    with open("sportscorer.wxs", "r") as f:
        soup = bs4.BeautifulSoup(f.read(), "xml")

    os.chdir((pathlib.Path(__file__).parent / "build").absolute())

    subprocess.run(
        ["wix", "extension", "add", "WixToolset.UI.wixext", "WixToolset.Heat"],
        check=True,
    )

    # set the version number
    soup.find("Wix").find("Package")["UpgradeCode"] = str(uuid.uuid4())

    download_embedded_python("staging_pythonembedded/python_embedded")

    # install packages from requirements.txt to staging_pythonembedded/python_embedded/Lib/site-packages
    subprocess.run(
        [
            "py",
            "-m",
            "pip",
            "install",
            "-r",
            "requirements.txt",
            "--target",
            "staging_pythonembedded/python_embedded/Lib/site-packages",
        ],
        check=True,
    )

    embedded_python_feature = soup.find("Feature", {"Id": "SportScorerEmbeddedPython"})
    install_dir = soup.find("Directory", {"Id": "PythonEmbed"})

    def list_directory(directory):
        for path in directory.iterdir():
            if path.is_dir():
                # create a directory element <Directory Id="uuid" Name="name">
                directory_element = soup.new_tag(
                    "Directory", Id="D" + uuid.uuid4().hex, Name=path.name
                )
                # create a component element <Component Id="uuid" Guid="uuid">
                embedded_python_component = soup.new_tag(
                    "Component", Id="C" + uuid.uuid4().hex, Guid=str(uuid.uuid4())
                )
                # add the directory element to the parent
                directory_element.append(embedded_python_component)

                # add the component to the feature
                embedded_python_feature.append(
                    soup.new_tag("ComponentRef", Id=embedded_python_component["Id"])
                )

                # recurse
                for child in list_directory(path):
                    if child.name == "Directory":
                        # add the child directory to the parent directory
                        directory_element.append(child)
                    elif child.name == "File":
                        # add the child file to the component
                        embedded_python_component.append(child)

                # yield the directory element
                yield directory_element
            else:
                # create a file element <File Id="uuid" Name="name" Source="path">
                file_element = soup.new_tag(
                    "File", Id="F" + uuid.uuid4().hex, Name=path.name, Source=str(path)
                )
                # yield the file element
                yield file_element

    embedded_python_component = soup.new_tag(
        "Component", Id="C" + uuid.uuid4().hex, Guid=str(uuid.uuid4())
    )
    embedded_python_feature.append(
        soup.new_tag("ComponentRef", Id=embedded_python_component["Id"])
    )
    install_dir.append(embedded_python_component)

    # add the files to the component
    for child in list_directory(pathlib.Path("staging_pythonembedded/python_embedded")):
        if child.name == "Directory":
            # add the child directory to the parent directory
            install_dir.append(child)
        elif child.name == "File":
            # add the child file to the component
            embedded_python_component.append(child)

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
