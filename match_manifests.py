#!/usr/bin/env python
import click
import subprocess
import os.path
import sys
import common
from typing import NamedTuple

@click.command()
@click.option("--basedir", default="~/code/ocp_repos", help="Base directory for repositories")
@click.option("--inputfile", default="manifests.txt", help="Name of input file for manifests")
@click.option("--output", default="-", help="Name of output file, - for stdout")

def match_manifests(basedir, inputfile, output):
    try:
        result = get_manifest_matches(basedir, inputfile)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    if output == "-":
        for m in result:
            print(m)
    else:
        with open(output, 'w') as f:
            for m in result:
                f.write(str(m) + "\n")

class ManifestRepositoryFile(NamedTuple):
    manifestRepo: common.ManifestRepository
    localFile: str
    def __repr__(self):
        return f"{self.manifestRepo} {self.localFile}"

    def __str__(self):
        return f"{self.manifestRepo} {self.localFile}"

def get_manifest_matches(basedir, inputfile):
    basedir = os.path.expanduser(basedir)
    with open(inputfile, "r") as f:
        reposText = f.read()
    manifestRepos = common.parse_manifest_repos_output(reposText)
    result = []
    for m in manifestRepos:
        mf = matchFile = match_local_file(basedir, m)
        result.append(mf)

    return result

def match_local_file(basedir, manifest):
    repodir = os.path.join(basedir, manifest.component)
    includes_manifests = False
    subdirs = []
    for f in os.scandir(repodir):
        if f.is_dir():
            if f.name == "manifests":
                includes_manifests = True
            else:
                subdirs.append(f.name)
    if includes_manifests:
        check_path = os.path.join(repodir, "manifests", manifest.originalFile)
        if os.path.exists(check_path):
            return ManifestRepositoryFile(manifest, check_path)

    for d in subdirs:
        check_path = os.path.join(repodir, d, manifest.originalFile)
        if os.path.exists(check_path):
            return ManifestRepositoryFile(manifest, check_path)

    return ManifestRepositoryFile(manifest, "MISSING")


if __name__ == '__main__':
    match_manifests()
