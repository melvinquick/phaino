import os
import shutil
import subprocess
import sys
from textwrap import dedent


def print_green(skk):
    print(f"\033[92m {skk}\033[00m")


def print_red(skk):
    print(f"\033[91m {skk}\033[00m")


def get_venv_path():
    home_dir = os.path.expanduser("~")
    venv_dir = os.path.join(home_dir, ".venvs")
    if not os.path.exists(venv_dir):
        os.makedirs(venv_dir)
    return os.path.join(venv_dir, "phaino_venv")


def get_desktop_file_path():
    return os.path.expanduser("~/.local/share/applications/phaino.desktop")


def create_venv(venv_path):
    print("Creating the virtual environment...", end=" ")
    sys.stdout.flush()
    subprocess.run(
        [sys.executable, "-m", "venv", venv_path],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print_green("[OK]")

    print("Ensuring pip is up to date...", end=" ")
    sys.stdout.flush()
    pip_path = os.path.join(venv_path, "bin", "pip")
    subprocess.run(
        [pip_path, "install", "--upgrade", "pip"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print_green("[OK]")


def install_app(venv_path):
    print("Installing Phaino into the virtual environment...", end=" ")
    sys.stdout.flush()
    pip_path = os.path.join(venv_path, "bin", "pip")
    subprocess.run(
        [pip_path, "install", "phaino"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print_green("[OK]")


def get_installed_version(venv_path):
    """Read version from installed package metadata inside the venv."""
    python_path = os.path.join(venv_path, "bin", "python3")
    result = subprocess.run(
        [
            python_path,
            "-c",
            "from importlib.metadata import version; print(version('phaino'))",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_icon(venv_path):
    site_packages = os.path.join(venv_path, "lib")
    for folder in os.listdir(site_packages):
        if folder.startswith("python"):
            site_packages = os.path.join(site_packages, folder, "site-packages")
            break
    icon_relative_path = "phaino/resources/images/phaino_bg_128.png"
    full_icon_path = os.path.join(site_packages, icon_relative_path)
    return full_icon_path


def get_python_path(venv_path):
    return os.path.join(venv_path, "bin", "python3")


def get_app_path(venv_path):
    return os.path.join(venv_path, "bin", "phaino")


def create_desktop_file(icon, version, python, app):
    print("Creating the .desktop entry...", end=" ")
    sys.stdout.flush()

    desktop_content = dedent(f"""\
        [Desktop Entry]
        Version={version}
        Type=Application
        Name=Phaino
        Comment=Password generator that never leaves your machine.
        Exec={python} {app}
        Icon={icon}
        Terminal=false
        Categories=Utility;
    """)

    desktop_path = get_desktop_file_path()
    os.makedirs(os.path.dirname(desktop_path), exist_ok=True)

    with open(desktop_path, "w") as f:
        f.write(desktop_content)
    print_green("[OK]")


def do_uninstall():
    """Removes venv and desktop file. Returns True if anything was removed."""
    venv_path = get_venv_path()
    desktop_file_path = get_desktop_file_path()
    removed = False

    if os.path.exists(venv_path):
        print("Removing the virtual environment...", end=" ")
        sys.stdout.flush()
        shutil.rmtree(venv_path)
        print_green("[OK]")
        removed = True

    if os.path.exists(desktop_file_path):
        print("Removing the .desktop entry...", end=" ")
        sys.stdout.flush()
        os.remove(desktop_file_path)
        print_green("[OK]")
        removed = True

    return removed


def do_install():
    """Fresh install: creates venv, installs app, creates desktop entry."""
    venv_path = get_venv_path()
    create_venv(venv_path)
    install_app(venv_path)

    # Dynamically read version from installed package metadata
    version = get_installed_version(venv_path)

    icon = get_icon(venv_path)
    python = get_python_path(venv_path)
    app = get_app_path(venv_path)
    create_desktop_file(icon, version, python, app)

    print()
    print_green(f"Phaino v{version} has been successfully installed.")


def handle_update():
    """Update = full uninstall followed by fresh install."""
    print("\nUpdating Phaino...\n")
    existed = do_uninstall()
    if not existed:
        print("No existing installation found. Performing fresh install.\n")
    else:
        print()
    do_install()


def show_menu():
    try:
        with open("/dev/tty", "r") as tty:
            while True:
                print("\n=== Phaino Installer ===")
                print("1) Install")
                print("2) Update")
                print("3) Uninstall")
                print("0) Exit")

                sys.stdout.write("\nSelect an option [0-3]: ")
                sys.stdout.flush()
                choice = tty.readline().strip()

                if choice == "1":
                    venv_path = get_venv_path()
                    if os.path.exists(venv_path):
                        print_red(
                            "\nExisting installation detected. Please use 'Update' instead."
                        )
                        continue
                    print()
                    do_install()
                    break

                elif choice == "2":
                    handle_update()
                    break

                elif choice == "3":
                    print()
                    if do_uninstall():
                        print()
                        print_green("Phaino has been uninstalled.")
                    else:
                        print("\nPhaino does not appear to be installed.")
                    break

                elif choice == "0":
                    print("\nGoodbye.")
                    break

                else:
                    print_red("\nInvalid selection. Please try again.")
    except OSError:
        print_red("Error: No interactive terminal available.")
        print_red("Please run this script from a terminal session.")
        sys.exit(1)


def main():
    show_menu()


if __name__ == "__main__":
    main()
