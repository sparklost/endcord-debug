import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request

LIB_NAMES = ("libopus.so", "libopus.dylib", "libopus-0.dll", "libopus.dll", "opus.dll")


def download(url, dest_path):
    """Download a file if it doesnt exist"""
    if not os.path.exists(dest_path):
        try:
            urllib.request.urlretrieve(url, dest_path)
        except Exception as e:
            raise OSError(f"Error downloading {url}: {e}")
    return dest_path


def get_env():
    """Environment for build commands, without foreign flag variables on windows"""
    env = os.environ.copy()
    if sys.platform == "win32":
        for name in ("CFLAGS", "CXXFLAGS", "CPPFLAGS", "LDFLAGS"):
            env.pop(name, None)
    return env


def run(cmd, cwd):
    """Run command and show its output on failure"""
    result = subprocess.run(cmd, cwd=cwd, env=get_env(), capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        log_path = os.path.join(cwd, "config.log")
        if os.path.exists(log_path):
            with open(log_path, "r", errors="replace", encoding="utf-8") as f:
                print("".join(f.readlines()[-80:]))
        raise subprocess.CalledProcessError(result.returncode, cmd)


def find_library(root):
    """Search directory tree for the first matching library file"""
    for folder, _, files in os.walk(root):
        for filename in files:
            if filename in LIB_NAMES:
                return os.path.abspath(os.path.join(folder, filename))
    return None


def build_libopus(build_dir="", opus_version="1.5.2"):
    """Build libopus"""
    print("  Downloading libopus release")
    opus_url = f"https://downloads.xiph.org/releases/opus/opus-{opus_version}.tar.gz"
    working_dir = os.path.join(build_dir, f"opus-{opus_version}")
    save_path = download(opus_url, os.path.join(build_dir, "opus.tar.gz"))
    with tarfile.open(save_path, "r:gz") as tar:
        tar.extractall(path=build_dir, filter="data")

    print("  Compiling libopus library")
    jobs = str(os.cpu_count() or 1)
    try:
        run(["sh", "./configure", "--disable-doc", "--disable-extra-programs"], working_dir)
        run(["make", f"-j{jobs}"], working_dir)
        return find_library(os.path.join(working_dir, ".libs"))
    except (subprocess.CalledProcessError, OSError):
        if sys.platform != "win32" or not shutil.which("cmake"):
            raise
        print("  configure/make failed, trying cmake")
        run([
            "cmake", "-S", ".", "-B", "cmake_build", "-G", "Ninja",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DBUILD_SHARED_LIBS=ON",
            "-DOPUS_BUILD_PROGRAMS=OFF",
            "-DOPUS_BUILD_TESTING=OFF",
        ], working_dir)
        run(["cmake", "--build", "cmake_build", "--config", "Release", "-j", jobs], working_dir)
        return find_library(os.path.join(working_dir, "cmake_build"))


if __name__ == "__main__":
    print(build_libopus())
