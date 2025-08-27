#!/usr/bin/env python3
"""
Launch a nightly test suite of the github test suite migration branches.
Merge the branch into the latest copy of trunk - send a message if conflicts occur
Temporary - edit the location of the clone
Launch a simple rose-stem suite
Apps,
UM,
Jules
"""

import os
import subprocess
import shutil
import argparse
from datetime import datetime

REPOS = {
    "lfric_apps": {
        "upstream": "git@github.com:MetOffice/lfric_apps.git",
        "downstream": "git@github.com:james-bruten-mo/lfric_apps.git",
        "branch": "lfric_apps_rose-stem",
        "groups": "developer",
    }
}


def run_command(command, shell=False):
    """
    Run a subprocess command and return the result object
    Inputs:
        - command, str with command to run
    Outputs:
        - result object from subprocess.run
    """
    if not shell:
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


def delete_clone(loc):

    if os.path.exists(loc):
        shutil.rmtree(loc)


def clone_upstream(repo, loc):

    commands = [
        f"git clone {REPOS[repo]["upstream"]} {loc}",
        f"git -C {loc} checkout trunk",
    ]
    for command in commands:
        run_command(command)


def set_remote(repo, loc):

    commands = [
        f"git -C {loc} remote add {repo}_fork {REPOS[repo]["downstream"]}",
        f"git -C {loc} fetch {repo}_fork",
    ]
    for command in commands:
        run_command(command)


def merge_branch(repo, loc):

    command = f"git -C {loc} merge {repo}_fork/{REPOS[repo]["branch"]}"
    run_command(command)


def launch_test_suite(repo, loc):

    date = datetime.today().strftime("%Y-%m-%d")
    command = (
        "cylc vip "
        f"-n gh_{repo}_{date} "
        f"-z g={REPOS[repo]["groups"]} "
        "-S USE_HEADS=true "
        f"{os.path.join(loc, "rose-stem")}"
    )
    run_command(command)


def update_clone_loc(repo, loc):
    """
    While cylc can't give us the location of the source, update the hardcoded location
    """

    conf_file = os.path.join(loc, "rose-stem", "rose-suite.conf")
    with open(conf_file, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith(f"{repo.upper()}_SOURCE"):
            line = line.split(":")
            lines[i] = f'{line[0]}:{loc}"\n'
            break

    with open(conf_file, "w") as f:
        for line in lines:
            f.write(line)


def parse_args():
    """
    Read command line args
    """

    parser = argparse.ArgumentParser("Pre-process and apply LFRic Apps upgrade macros.")
    parser.add_argument(
        "repo",
        choices=list(REPOS.keys()),
        help=f"The target repo name. Must be in {list(REPOS.keys())}",
    )
    return parser.parse_args()


def main():

    args = parse_args()

    print(
        f"Launching nightly testing for {args.repo} "
        f"on {datetime.today().strftime('%Y-%m-%d')}"
    )

    clone_loc = os.path.expanduser((os.path.join("~", "github_nightly_testing")))
    run_command(f"mkdir -p {clone_loc}")

    loc = os.path.join(clone_loc, args.repo)

    delete_clone(loc)

    clone_upstream(args.repo, os.path.join(clone_loc, args.repo))

    set_remote(args.repo, loc)

    merge_branch(args.repo, loc)

    update_clone_loc(args.repo, loc)

    launch_test_suite(args.repo, loc)


if __name__ == "__main__":
    main()
