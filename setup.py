import os
import platform
import zipfile
from pathlib import Path
from urllib.request import urlretrieve, Request, urlopen

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

# Import version from the package
import sys

sys.path.insert(0, "confsec")
from _version import LIBCONFSEC_VERSION


def get_platform_info():
    """Get the OS and architecture for the current platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Map platform.system() output to our naming convention
    if system == "darwin":
        os_name = "darwin"
    elif system == "linux":
        os_name = "linux"
    else:
        raise RuntimeError(f"Unsupported operating system: {system}")

    # Map platform.machine() output to our naming convention
    if machine in ("x86_64", "amd64"):
        arch = "amd64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")

    return os_name, arch


class BuildLibconfsec(build_ext):
    """Custom build command to download libconfsec binary."""

    def run(self):
        """Download and extract libconfsec for the current platform, or use local files if specified."""
        # Check if we should use local libconfsec files
        use_local = os.environ.get("USE_LOCAL_LIBCONFSEC", "").lower() in (
            "1",
            "true",
            "yes",
        )

        lib_dir = Path("confsec") / "lib"
        lib_dir.mkdir(parents=True, exist_ok=True)

        if use_local:
            print("Using local libconfsec files from confsec/lib/")
            # Verify that required local files exist
            required_files = ["libconfsec.a", "libconfsec.h"]
            missing_files = []
            for lib_filename in required_files:
                if not (lib_dir / lib_filename).exists():
                    missing_files.append(lib_filename)

            if missing_files:
                raise RuntimeError(
                    f"USE_LOCAL_LIBCONFSEC is set but missing files: {', '.join(missing_files)}"
                )
        else:
            # Download libconfsec binary
            os_name, arch = get_platform_info()

            # Clear out any existing libconfsec files
            for file in lib_dir.iterdir():
                if file.name.startswith("libconfsec_"):
                    file.unlink()

            # Download URL
            tag = f"libconfsec%2Fv{LIBCONFSEC_VERSION}"
            lib_filename = f"libconfsec_{os_name}_{arch}.zip"
            lib_url = f"https://github.com/confidentsecurity/libconfsec/releases/download/{tag}/{lib_filename}"
            sha_filename = f"{lib_filename}.sha256"
            sha_url = f"https://github.com/confidentsecurity/libconfsec/releases/download/{tag}/{lib_filename}.sha256"

            # Download and extract
            zip_path = lib_dir / lib_filename
            sha_path = lib_dir / sha_filename
            print(f"Downloading libconfsec from {lib_url}")

            # Check for GitHub token for private repo access
            github_token = os.environ.get("GITHUB_TOKEN")
            if github_token:
                headers = {"Authorization": f"Bearer {github_token}"}
                req = Request(lib_url, headers=headers)
                with urlopen(req) as response, open(zip_path, "wb") as f:
                    f.write(response.read())
                req = Request(sha_url, headers=headers)
                with urlopen(req) as response, open(sha_path, "wb") as f:
                    f.write(response.read())
            else:
                urlretrieve(lib_url, zip_path)
                urlretrieve(sha_url, sha_path)

            print(f"Extracting {zip_path}")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(lib_dir)

            # Clean up zip file
            zip_path.unlink()

        super().run()


def create_extension():
    """Create the extension module with platform-specific settings."""
    os_name, arch = get_platform_info()

    confsec_c_path = "confsec/libconfsec/libconfsec_py.c"
    lib_path = "confsec/lib/libconfsec.a"
    include_path = "confsec/lib"

    # Platform-specific compiler/linker flags
    extra_compile_args = []
    extra_link_args = []

    if os_name == "darwin":
        if arch == "arm64":
            extra_compile_args = ["-arch", "arm64"]
            extra_link_args = ["-arch", "arm64"]
        elif arch == "amd64":
            extra_compile_args = ["-arch", "x86_64"]
            extra_link_args = ["-arch", "x86_64"]

    return Extension(
        "confsec.libconfsec.libconfsec_py",
        sources=[confsec_c_path],
        extra_objects=[lib_path],
        include_dirs=[include_path],
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    )


if __name__ == "__main__":
    setup(
        ext_modules=[create_extension()],
        cmdclass={
            "build_ext": BuildLibconfsec,
        },
        package_data={
            "confsec": ["lib/*"],
        },
    )
