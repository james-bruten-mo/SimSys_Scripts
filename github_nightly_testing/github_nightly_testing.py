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
from update_dependencies import update_dependencies

REPOS = {
    "lfric_apps": {
        "mirror_loc": "/data/users/gitassist/git_mirrors/MetOffice/lfric_apps.git",
        "mirror_fetch": "james-bruten-mo/lfric_apps_rose-stem",
        "groups": "azspice",
    },
    "lfric_core": {
        "mirror_loc": "/data/users/gitassist/git_mirrors/MetOffice/lfric_core.git",
        "mirror_fetch": "james-bruten-mo/lfric_core_git_test",
        "groups": "all",
    },
    "um": {
        "mirror_loc": "/data/users/gitassist/git_mirrors/MetOffice/um.git",
        "mirror_fetch": "james-bruten-mo/um_git_test",
        "groups": "all",
    },
    "jules": {
        "mirror_loc": "/data/users/gitassist/git_mirrors/MetOffice/jules.git",
        "mirror_fetch": "james-bruten-mo/jules_git_test",
        "groups": "all",
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

def clone_mirror(repo, loc):

    commands = (
        f"git clone {REPOS[repo]['mirror_loc']} {loc}",
        f"git -C {loc} fetch origin {REPOS[repo]['mirror_fetch']}",
        f"git -C {loc} checkout FETCH_HEAD"
    )
    for command in commands:
        run_command(command)


def merge_branch(loc):

    command = f"git -C {loc} merge --no-edit origin/trunk"
    run_command(command)


def launch_test_suite(repo, loc):

    date = datetime.today().strftime("%Y-%m-%d")
    command = (
        "cylc vip "
        f"-n gh_{repo}_{date} "
        f"-z g={REPOS[repo]['groups']} "
        "-S USE_MIRRORS=true "
        f"{os.path.join(loc, 'rose-stem')}"
    )
    run_command(command)


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

    clone_mirror(args.repo, os.path.join(clone_loc, args.repo))

    merge_branch(loc)

    launch_test_suite(args.repo, loc)


if __name__ == "__main__":
    main()
