#!/usr/bin/python
import yaml
import subprocess
import tempfile
import re
import shutil
import argparse
from pathlib import Path


def write_new_ref(dependencies_file, dependency, new_ref):
    print(f"Writing ref for {dependency}")

    with open(dependencies_file, "r") as f:
        lines = f.readlines()

    in_section = False
    for i, line in enumerate(lines):
        if line.startswith(f"{dependency}:"):
            in_section = True
        if in_section and "ref:" in line:
            line = line.split(":")
            line[-1] = new_ref
            line = f"{line[0]}: {line[1]}\n"
            lines[i] = line
            break

    with open(dependencies_file, "w") as f:
        for line in lines:
            f.write(line)


def run_command(command, shell=False, rval=True):
    """
    Run a subprocess command and return the result object
    Inputs:
        - command, str with command to run
    Outputs:
        - result object from subprocess.run
    """
    # print(command)
    if not shell and type(command) is not list:
        command = command.split()
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=300,
        shell=shell,
        check=False,
    )
    if result.returncode:
        print(result.stdout, end="\n\n\n")
        raise RuntimeError(
            f"[FAIL] Issue found running command {command}\n\n{result.stderr}"
        )
    if rval:
        return result


def get_latest_hash(dependency, values):
    branch = "trunk"
    if dependency.lower() in ("simsys_scripts", "mule", "shumlib", "jules", "um_meta", "um_aux", "ukca"):
        branch = "main"
    tmpdir = tempfile.mkdtemp()
    commands = (
        f"git -C {tmpdir} init",
        f"git -C {tmpdir} remote add upstream {values['source']}",
        f"git -C {tmpdir} fetch upstream",
    )
    for command in commands:
        run_command(command)
    command = f"git -C {tmpdir} log --pretty=format:'%H' -n 1 upstream/{branch}"
    result = run_command(command, rval=True)
    shutil.rmtree(tmpdir)
    return result.stdout


def update_dependencies(dependencies_file):

    rval = False

    with open(dependencies_file, "r") as stream:
        dependencies = yaml.safe_load(stream)

    for dependency, values in dependencies.items():
        if not values["source"] or not values["ref"]:
            continue
        if ".git" not in values["source"]:
            continue
        if not re.match(r"^\s*([0-9a-f]{40})\s*$", values["ref"]):
            continue
        new_ref = get_latest_hash(dependency, values)
        new_ref = new_ref.strip("'\"")
        if new_ref != str(values["ref"]):
            write_new_ref(dependencies_file, dependency, new_ref)
            rval = True

    return rval


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dependencies", help="Path to dependencies.yaml file")
    args = parser.parse_args()
    dependencies_file = Path(args.dependencies) / "dependencies.yaml"
    update_dependencies(dependencies_file)
