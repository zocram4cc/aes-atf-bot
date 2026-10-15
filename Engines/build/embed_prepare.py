#!/usr/bin/env python3
"""
Embeddable Python Preparation Script

This script automatically downloads, prepares, and optimizes a fresh embeddable Python release
"""

import os
import re
import sys
import glob
import json
#import time
import shutil
import zipfile
import subprocess
import importlib.util
import urllib.request

if importlib.util.find_spec("rich") is not None:
    from rich import print
    from rich.traceback import install as install_rich_traceback
    install_rich_traceback(show_locals=True)
else:
    print("[WARNING] Rich not found, color tags will not be processed")
    print("[WARNING] Close this window and run \"pip install rich\" to install it")
    print("")
    input("Or press Enter to continue... ")


PYTHON_VERSION = "3.13"
PYTHON_GITHUB_SOURCE = "adang1345/PythonVista"
PYTHON_SUFFIX = "embed-amd64"


def log(message):
    """Log a message with rich formatting."""
    print(f"[bold blue]\\[EMBED_PREPARE][/bold blue] {message}")

def get_latest_python_version():
    """Find the latest Python version matching PYTHON_VERSION on the source GitHub."""
    try:
        # GitHub API to get all releases
        api_url = f"https://api.github.com/repos/{PYTHON_GITHUB_SOURCE}/contents/"
        log(f"Searching for latest Python {PYTHON_VERSION}.x version...")

        response = urllib.request.urlopen(api_url)
        if response.status != 200:
            raise Exception(f"GitHub API request failed with status {response.status}")

        data = json.loads(response.read().decode('utf-8'))
        response.close()

        # Find all directories that match our version pattern
        version_pattern = re.compile(rf"^{re.escape(PYTHON_VERSION)}\.(\d+)$")
        matching_versions = []

        for item in data:
            if item['type'] == 'dir':
                match = version_pattern.match(item['name'])
                if match:
                    patch_version = int(match.group(1))
                    matching_versions.append((patch_version, item['name']))

        if not matching_versions:
            raise Exception(f"No Python {PYTHON_VERSION}.x versions found")

        # Get the latest version (highest patch number)
        # Sort by patch version number and get the last one
        matching_versions.sort()  # Sort by first element (patch number) by default
        latest_patch_number, latest_version = matching_versions[-1]
        log(f"Found latest version: {latest_version}")
        return latest_version

    except Exception as e:
        log(f"Error finding latest Python version: {e}")
        log("Falling back to manual version specification")
        return None

def download_and_extract_python():
    """Download and extract the latest embeddable Python release."""
    # Get the latest version
    version = get_latest_python_version()
    if not version:
        print("[bold red]Could not determine latest Python version.[/bold red]")
        print("Please check the version manually at:")
        print(f"[blue]https://github.com/{PYTHON_GITHUB_SOURCE}[/blue]")
        return None

    # Construct download URL
    filename = f"python-{version}-{PYTHON_SUFFIX}.zip"
    download_url = f"https://raw.githubusercontent.com/{PYTHON_GITHUB_SOURCE}/master/{version}/{filename}"

    # Create embed folder in parent directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)  # Go up from build/ to Engines/
    embed_path = os.path.join(parent_dir, "embed")

    # Clean up existing embed folder
    if os.path.exists(embed_path):
        log(f"Removing existing embed folder: {embed_path}")
        shutil.rmtree(embed_path)

    os.makedirs(embed_path, exist_ok=True)

    # Download the Python release
    zip_path = os.path.join(embed_path, filename)
    log(f"Downloading {filename}...")
    log(f"URL: {download_url}")

    try:
        urllib.request.urlretrieve(download_url, zip_path)
        log(f"Downloaded to {zip_path}")
    except Exception as e:
        log(f"Error downloading Python release: {e}")
        return None

    # Extract the ZIP file
    log("Extracting embeddable Python...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(embed_path)

        # Remove the ZIP file
        os.remove(zip_path)
        log(f"Extracted embeddable Python to {embed_path}")
        return embed_path

    except Exception as e:
        log(f"Error extracting Python release: {e}")
        return None

def get_dependencies():
    """Get dependencies by importing REQUREMENTS from the utils directory."""
    try:
        # Add the parent directory to Python path temporarily
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)  # Go up from build/ to Engines/

        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        # Import the DEPENDENCIES from REQUREMENTS.py
        from REQUIREMENTS import DEPENDENCIES

        # Extract name_pip from each dependency dict
        dependencies = []
        for dep in DEPENDENCIES:
            dep_name = dep["name_pip"]
            if dep["version"] != "any":
                dep_name += dep["version"]
            dependencies.append(dep_name)

        return dependencies

    except Exception as e:
        log(f"Error getting dependencies from REQUREMENTS.py:\\n{e}")
        sys.exit(1)

def download_get_pip(embed_path):
    """Download get-pip.py to the embed folder."""
    get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
    get_pip_path = os.path.join(embed_path, "get-pip.py")

    log("Downloading get-pip.py...")
    try:
        urllib.request.urlretrieve(get_pip_url, get_pip_path)
        log(f"Downloaded get-pip.py to {get_pip_path}")
        return get_pip_path
    except Exception as e:
        log(f"Error downloading get-pip.py: {e}")
        return None

def install_pip(embed_path, python_exe):
    """Install pip using get-pip.py."""
    get_pip_path = os.path.join(embed_path, "get-pip.py")

    if not os.path.exists(get_pip_path):
        get_pip_path = download_get_pip(embed_path)
        if not get_pip_path:
            return False

    log("Installing pip...")
    try:
        result = subprocess.run(
            [python_exe, get_pip_path],
            cwd=embed_path, capture_output=True, text=True
            )
        if result.returncode == 0:
            log("pip installed successfully")

            # Verify pip installation by testing it directly
            log("Verifying pip installation...")
            test_result = subprocess.run(
                [python_exe, "-m", "pip", "--version"],
                cwd=embed_path, capture_output=True, text=True
                )
            if test_result.returncode == 0:
                log(f"pip verification successful: {test_result.stdout.strip()}")
                return True
            else:
                log(f"pip verification failed: {test_result.stderr}")
                return False
        else:
            log(f"pip installation failed: {result.stderr}")
            return False
    except Exception as e:
        log(f"Error installing pip: {e}")
        return False


def install_dependencies(embed_path, python_exe):
    """Install required dependencies."""
    dependencies = get_dependencies()

    log(f"Installing dependencies: {', '.join(dependencies)}")

    # First, verify pip is still accessible
    log("Verifying pip accessibility before dependency installation...")
    test_result = subprocess.run(
        [python_exe, "-m", "pip", "--version"],
        cwd=embed_path, capture_output=True, text=True
        )
    if test_result.returncode != 0:
        log(f"pip is not accessible: {test_result.stderr}")
        log("This may be due to path caching issues with embeddable Python")
        return False

    try:
        build_tools_cmd = [python_exe, "-m", "pip", "install", "setuptools", "wheel", "-t", ".\\Lib\\site-packages"]
        log(f"Installing build tools: {' '.join(build_tools_cmd)}")
        build_tools_result = subprocess.run(build_tools_cmd, cwd=embed_path, capture_output=True, text=True)
        if build_tools_result.returncode != 0:
            log(f"Build tools installation failed with exit code {build_tools_result.returncode}")
            if build_tools_result.stderr:
                log(f"Error output: {build_tools_result.stderr}")
            if build_tools_result.stdout:
                log(f"Standard output: {build_tools_result.stdout}")
            return False

        cmd = [python_exe, "-m", "pip", "install"] + dependencies + ["-t", ".\\Lib\\site-packages"]
        log(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=embed_path, capture_output=True, text=True)

        if result.returncode == 0:
            log("Dependencies installed successfully")
            if result.stdout:
                log(f"pip output: {result.stdout}")
            return True
        else:
            log(f"Dependency installation failed with exit code {result.returncode}")
            if result.stderr:
                log(f"Error output: {result.stderr}")
            if result.stdout:
                log(f"Standard output: {result.stdout}")
            return False
    except Exception as e:
        log(f"Error installing dependencies: {e}")
        return False

# Import all other functions from the original script
def remove_pip_and_get_pip(embed_path):
    """Remove pip, Scripts folder, and get-pip.py to save space."""
    site_packages = os.path.join(embed_path, "Lib", "site-packages")

    # Remove pip
    pip_paths = [
        os.path.join(site_packages, "pip"),
        os.path.join(site_packages, "pip-*"),
    ]

    for pattern in pip_paths:
        for path in glob.glob(pattern):
            if os.path.exists(path):
                log(f"Removing {path}")
                shutil.rmtree(path, ignore_errors=True)

    # Remove Scripts folder (contains pip.exe and other executables)
    scripts_path = os.path.join(embed_path, "Scripts")
    if os.path.exists(scripts_path):
        log("Removing Scripts folder")
        shutil.rmtree(scripts_path, ignore_errors=True)

    # Remove get-pip.py
    get_pip_path = os.path.join(embed_path, "get-pip.py")
    if os.path.exists(get_pip_path):
        log("Removing get-pip.py")
        os.remove(get_pip_path)

def create_cryptodome_stub(site_packages_path):
    """Replace Cryptodome with minimal stub by copying from build/stubs."""
    cryptodome_path = os.path.join(site_packages_path, "Cryptodome")

    if os.path.exists(cryptodome_path):
        log("Removing original Cryptodome")
        shutil.rmtree(cryptodome_path)

    # Remove Cryptodome dist-info
    for item in os.listdir(site_packages_path):
        if item.startswith("pycryptodomex-") and item.endswith(".dist-info"):
            shutil.rmtree(os.path.join(site_packages_path, item))

    log("Creating Cryptodome stub")

    # Get path to stub files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stub_source = os.path.join(script_dir, "stubs", "Cryptodome")

    # Copy the entire stub directory structure
    shutil.copytree(stub_source, cryptodome_path)

def _remove_library_files(directory_path, kept_files):
    """Helper to remove files and their corresponding .pyc files from a library subdirectory.

    Args:
        directory_path: Path to the directory to clean
        kept_files: List of filenames to keep (should include __pycache__)

    Returns:
        Number of files removed
    """
    if not os.path.exists(directory_path):
        return 0

    removed_count = 0
    removed_files = []

    # Remove source files that aren't in the keep list
    for item in os.listdir(directory_path):
        if item not in kept_files:
            item_path = os.path.join(directory_path, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
                removed_files.append(os.path.splitext(item)[0])  # Store base name
                removed_count += 1

    # Remove corresponding .pyc files
    pycache_path = os.path.join(directory_path, "__pycache__")
    if os.path.exists(pycache_path):
        for pyc_file in os.listdir(pycache_path):
            if pyc_file.endswith('.pyc'):
                base_name = pyc_file.split('.')[0]  # Get name before .cpython-313.pyc
                if base_name in removed_files:
                    os.remove(os.path.join(pycache_path, pyc_file))

    return removed_count

def optimize_pygments(site_packages_path):
    """Remove unnecessary pygments lexers, styles, and formatters.

    Rich only needs:
    - Python lexer for traceback syntax highlighting
    - Token definitions
    - Core lexer infrastructure

    This removes the unused lexers for 250+ languages.
    """
    pygments_path = os.path.join(site_packages_path, "pygments")

    if not os.path.exists(pygments_path):
        log("Warning: pygments not found, skipping optimization")
        return

    log("Optimizing pygments (removing unused lexers, styles, formatters)")

    # Remove all styles (Rich uses its own ANSI color mappings)
    styles_path = os.path.join(pygments_path, "styles")
    _remove_library_files(styles_path, ["__init__.py", "_mapping.py", "__pycache__"])
    log("  Removed styles and their .pyc files")

    # Remove all formatters (Rich renders internally)
    formatters_path = os.path.join(pygments_path, "formatters")
    _remove_library_files(formatters_path, ["__init__.py", "_mapping.py", "__pycache__"])
    log("  Removed formatters and their .pyc files")

    # Remove all lexers except Python (Rich only highlights Python code in tracebacks)
    lexers_path = os.path.join(pygments_path, "lexers")
    kept_lexers = ["__init__.py", "_mapping.py", "python.py", "__pycache__"]
    removed_count = _remove_library_files(lexers_path, kept_lexers)
    log(f"  Removed {removed_count} unused lexers and their .pyc files (kept only python.py)")

    # Remove command-line tools (only those not imported internally)
    # Build kept files list by excluding the unnecessary modules
    unnecessary_modules = ["cmdline.py", "__main__.py", "console.py", "sphinxext.py"]
    all_items = set(os.listdir(pygments_path))
    kept_files = list(all_items - set(unnecessary_modules))
    _remove_library_files(pygments_path, kept_files)

    log("Pygments optimization complete")

def get_modules_with_pyd_files(site_packages_path):
    """Get list of modules that contain .pyd files."""
    modules_with_pyd = set()

    for root, dirs, files in os.walk(site_packages_path):
        for file in files:
            if file.endswith('.pyd'):
                rel_path = os.path.relpath(root, site_packages_path)
                if rel_path == '.':
                    modules_with_pyd.add(file)
                else:
                    module_name = rel_path.split(os.sep)[0]
                    modules_with_pyd.add(module_name)

    return modules_with_pyd

def get_essential_files(site_packages_path, modules_with_pyd):
    """Get list of essential files that must be extracted (not zipped)."""
    essential_files = set()

    # Add all .pyd files
    for root, dirs, files in os.walk(site_packages_path):
        for file in files:
            if file.endswith('.pyd'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, site_packages_path)
                essential_files.add(rel_path)

    # Add essential Python files for modules with .pyd files
    essential_patterns = {
        'bcj': ['__init__.py', '_bcjfilter.py', 'py.typed'],
        'charset_normalizer': '*',  # Keep all charset_normalizer files
        'inflate64': ['__init__.py'],
        'psutil': ['__init__.py'],
        'pyppmd': ['__init__.py', 'c/c_ppmd.py'],
        'pyzstd': ['__init__.py', '_zstdfile.py', '_seekable_zstdfile.py', '_c/__init__.py']
    }

    for module in modules_with_pyd:
        if module in essential_patterns:
            patterns = essential_patterns[module]
            if patterns == '*':
                # Keep all files for this module
                module_path = os.path.join(site_packages_path, module)
                if os.path.exists(module_path):
                    for root, dirs, files in os.walk(module_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, site_packages_path)
                            essential_files.add(rel_path)
            else:
                # Keep specific files
                for pattern in patterns:
                    file_path = os.path.join(site_packages_path, module, pattern)
                    if os.path.exists(file_path):
                        rel_path = os.path.relpath(file_path, site_packages_path)
                        essential_files.add(rel_path)

    return essential_files

def create_site_packages_zip(site_packages_path):
    """Create site-packages.zip with non-essential files."""
    zip_path = os.path.join(os.path.dirname(site_packages_path), "site-packages.zip")

    # Get modules with .pyd files and essential files to keep extracted
    modules_with_pyd = get_modules_with_pyd_files(site_packages_path)
    essential_files = get_essential_files(site_packages_path, modules_with_pyd)

    log(f"Found modules with .pyd files: {modules_with_pyd}")
    log(f"Keeping {len(essential_files)} essential files extracted")

    # Create ZIP with non-essential files
    files_zipped = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(site_packages_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, site_packages_path)

                # Skip essential files (they stay extracted)
                if rel_path not in essential_files:
                    zf.write(file_path, rel_path)
                    files_zipped += 1

    log(f"Created site-packages.zip with {files_zipped} files")

    # Remove non-essential files from site-packages directory
    files_removed = 0
    for root, dirs, files in os.walk(site_packages_path, topdown=False):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, site_packages_path)

            if rel_path not in essential_files:
                os.remove(file_path)
                files_removed += 1

        # Remove empty directories
        try:
            if not os.listdir(root) and root != site_packages_path:
                os.rmdir(root)
        except OSError:
            pass

    log(f"Removed {files_removed} non-essential files from site-packages")
    return zip_path

def setup_pth_file(embed_path, enable_site=False, include_zip=False):
    """Configure python*._pth file with specified options."""
    pth_files = glob.glob(os.path.join(embed_path, "python*._pth"))

    if not pth_files:
        log("Warning: No python*._pth file found")
        return

    pth_file = pth_files[0]

    # Extract Python version from filename
    filename = os.path.basename(pth_file)
    version = filename.replace("python", "").replace("._pth", "")

    # Build content based on options
    pth_lines = [
        f"python{version}.zip",
        "Lib",
        "Lib\\site-packages"
    ]

    if include_zip:
        pth_lines.append("Lib\\site-packages.zip")

    pth_lines.extend([".", "..", ""])
    pth_lines.append("# Uncomment to run site.main() automatically")

    if enable_site:
        pth_lines.append("import site")
        config_type = "basic configuration for pip installation"
    else:
        pth_lines.append("#import site")
        config_type = "final optimized configuration"

    pth_content = "\n".join(pth_lines) + "\n"

    log(f"Setting up {os.path.basename(pth_file)} with {config_type}")
    with open(pth_file, 'w') as f:
        f.write(pth_content)

def main():
    print("[bold green]Embeddable Python Builder[/bold green]")
    print("Automatically downloading and preparing optimized Python distribution...")
    print()

    # Step 1: Download and extract embeddable Python
    embed_path = download_and_extract_python()
    if not embed_path:
        print("[bold red]✗ Failed to download embeddable Python[/bold red]")
        return 1

    # Find python.exe
    python_exe = os.path.join(embed_path, "python.exe")
    if not os.path.exists(python_exe):
        log(f"Error: python.exe not found in {embed_path}")
        return 1

    log(f"Preparing embeddable Python in: {embed_path}")

    # Step 2: Set up pth configuration for pip installation
    setup_pth_file(embed_path, enable_site=True)

    # Step 3: Install pip
    if not install_pip(embed_path, python_exe):
        print("\n[bold red]✗ Failed to install pip[/bold red]")
        return 1

    # Step 4: Install dependencies
    if not install_dependencies(embed_path, python_exe):
        print("\n[bold red]✗ Failed to install dependencies[/bold red]")
        return 1

    # Step 5: Remove pip and get-pip.py
    remove_pip_and_get_pip(embed_path)

    site_packages_path = os.path.join(embed_path, "Lib", "site-packages")

    # Step 6: Replace Cryptodome with stub
    #create_cryptodome_stub(site_packages_path)

    # Step 7: Optimize pygments (remove unused lexers, styles, formatters)
    optimize_pygments(site_packages_path)

    # Step 8: Wait 2 seconds then create site-packages.zip
    #time.sleep(2)
    #zip_path = create_site_packages_zip(site_packages_path)

    # Step 9: Finalize pth file with optimized configuration
    setup_pth_file(embed_path, enable_site=False, include_zip=False)

    print("\n[bold green]✓ Embeddable Python preparation completed successfully[/bold green]")
    #log(f"Site-packages.zip created: {zip_path}")
    log(f"Embeddable Python ready at: {embed_path}")

    # Show final size info
    #if os.path.exists(zip_path):
    #    zip_size = os.path.getsize(zip_path) / (1024 * 1024)
    #    log(f"ZIP size: {zip_size:.1f} MB")

    extracted_size = sum(
        os.path.getsize(os.path.join(root, file))
        for root, dirs, files in os.walk(site_packages_path)
        for file in files
    ) / (1024 * 1024)
    log(f"Extracted size: {extracted_size:.1f} MB")

    return 0

if __name__ == "__main__":
    sys.exit(main())