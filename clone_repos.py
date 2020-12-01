#!/usr/bin/env python
import click
import os.path
import os
import sys
import subprocess
import common

@click.command()
@click.option("--basedir", default=".", help="Base directory where repositories should be created")
@click.option("--branch", default="roks_profile", help="Name of branch to create in each repository")
@click.option("--inputfile", default="manifests.txt", help="Name of input file for manifests")

def create_repos(basedir, branch, inputfile):
    try:
        do_create_repos(basedir, branch, inputfile)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)

def do_create_repos(basedir, branch, inputfile):
    basedir = os.path.expanduser(basedir)
    # Ensure that the base directory exists
    if not os.path.exists(basedir):
        os.makedirs(basedir)

    # Obtain list of repos
    with open(inputfile, 'r') as f:
        repotext = f.read()

    repos = common.parse_manifest_repos_output(repotext)

    # Clone each repository and fork it, create a working branch
    for repo in repos:
        repo_path = os.path.join(basedir, repo.component)
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)
            print(f"Cloning repository {repo.component} with url {repo.repository}")
            subprocess.run(["git", "clone", repo.repository, "."], cwd=repo_path, check=True)
            subprocess.run(["gh", "repo", "fork", "--remote"], cwd=repo_path, check=True)
            subprocess.run(["git", "checkout", "-b", branch, "upstream/master"], cwd=repo_path, check=True)


if __name__ == '__main__':
    create_repos()
