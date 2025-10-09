#!/usr/bin/env python3

from pathlib import Path
import subprocess
from update_dependencies import update_dependencies


def run_command(command, shell=False):
    """
    Run a subprocess command and return the result object
    Inputs:
        - command, str with command to run
    Outputs:
        - result object from subprocess.run
    """
    if not shell and isinstance(command, str):
        command = command.split()
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=300,
        shell=shell,
        check=False,
    )
    return result


def update_clone(path):
    """
    Merge in trunk latest and update dependencies if um/apps
    """

    print(f"Fetching upstream for {path}")
    command = f"git -C {path} fetch upstream"
    result = run_command(command)
    if result.returncode:
        print(f"Failure fetching upstream for {clone}\n{result.stderr}")
        return

    print(f"Merging trunk into {path}")
    command = f"git -C {path} merge --no-edit upstream/trunk"
    result = run_command(command)
    if result.returncode:
        print(f"Failure merging trunk into {clone}\n{result.stderr}")
        return

    print(f"Pushing from {path}")
    command = f"git -C {path} push"
    result = run_command(command)
    if result.returncode:
        print(f"Failure pushing from {clone}\n{result.stderr}")
        return

    if "lfric_apps" in str(path) or "um" in str(path):
        print(f"Updating Dependencies for {path}")
        try:
            update_dependencies(path / "dependencies.yaml")
        except:
            print(f"Error updating dependencies for {path}")

    print()


start_path = Path("/var/tmp/persistent/fork_clones/test_suites")

for clone in (
    "um",
    "jules",
    "lfric_apps",
    "lfric_core",
    "ukca",
):
    path = start_path / clone
    update_clone(path)
