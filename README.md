# Cluster Profiles Automation
Scripts to help automating cluster profile annotations on OpenShift release manifests

## Prerequisites

- Github CLI (https://github.com/cli/cli)
- Modified `oc` command:
  Clone `https://github.com/csrwng/oc/tree/cluster_profiles` and run `make build`
- `manifest-annotator` command from `https://github.com/csrwng/manifest-annotator`:
  run `go build .` and put resulting binary in the path
- For python, you need the following modules:
  - click
  - pyyaml

  Install with `pip install MODULE`

## Cloning Release Repositories

1. Obtain listing of manifests with their respective repositories:
   `oc adm release info --repos-with-manifests CI_IMAGE > manifests.txt`
   where CI_IMAGE is a recent image from https://openshift-release.apps.ci.l2s4.p1.openshiftapps.com/
   If you have a quay.io pull secret in a separate file, you'll need to add:
   `--registry-config PULL_SECRET_FILE_PATH` to the command above.
   The result of the above command should be a space-separated file that contains the following
   columns: 1) component, 2) git repo, 3) filename in repo, 4) filename in release payload.

2. Use the clone-repos.py script to create local clones of all the repos in the manifests.txt file:
   `./clone_repos.py --basedir BASE_DIRECTORY --branch YOUR_BRANCH --inputfile manifests.txt`
   BASE_DIRECTORY is the directory in your machine where you want to place all cloned repositories,
   YOUR_BRANCH is the branch name you want to use for your modifications. This script uses
   `gh repo fork` which will fork repositories that you don't have a fork of, and reuse your existing
   fork if you have one. If cloning fails at some point, simply re-run the command above. It will skip
   repositories for which a directory already exists.

## Applying Your Annotation to Manifests

1. Match manifests in release image to files on your computer with `match-manifests.py`. Run:
   `match-manifests.py --basedir BASE_DIRECTORY --inputfile manifests.txt > manifests-with-files.txt`
   Where BASE_DIRECTORY is the same directory you used to clone the repositories above.
   This command outputs the list of manifests matched with files on your machine. For files not found,
   it uses a placeholder `MISSING`.

2. Obtain a list of files to annotate:
   `cat manifests-with-files.txt | awk '{ print $5 }' | grep -v MISSING > files-to-annotate.txt`

3. Modify the `annotate.sh` script in this repo to use the annotation that you want to set.

4. Annotate all files with `cat files-to-annotate.txt | xargs ./annotate.sh`


## Committing your changes and creating PRs

This part is not automated because you will likely need to make manual changes to some repos because they
vendor manifests from `github.com/openshift/api`.
(Look at all files that are labeled MISSING in manifests-with-files.txt)

However, creating pull requests is greatly simplified with the `gh` command. When you are ready, use
`gh pr create --title "blah" --body "blah"`
