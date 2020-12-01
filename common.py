import urllib3
import json
import sys
import yaml
import subprocess
from typing import NamedTuple
from typing import List

class Config(NamedTuple):
    releaseStream: str
    releaseImage: str
    pullSecret: str

class ManifestRepository(NamedTuple):
    component: str
    repository: str
    originalFile: str
    releaseFile: str
    def __repr__(self):
        return f"{self.component} {self.repository} {self.originalFile} {self.releaseFile}"

    def __str__(self):
        return f"{self.component} {self.repository} {self.originalFile} {self.releaseFile}"

class Manifest(NamedTuple):
    fileName: str
    kind: str
    groupVersion: str
    name: str
    namespace: str

    def __repr__(self):
        return f"{self.fileName} {self.kind} {self.groupVersion} {self.name} {self.namespace}"

    def __str__(self):
        return f"{self.fileName} {self.kind} {self.groupVersion} {self.name} {self.namespace}"

class RepoWithManifests(NamedTuple):
    name: str
    repofiles: List
    manifests: List

def read_config(filename):
    with open(filename) as file:
        config_dict = yaml.full_load(file)
        return Config(**config_dict)

def parse_manifest_repos_output(result):
    repos = []
    for line in result.splitlines():
        parts = line.split(" ")
        if len(parts) < 4:
            continue
        r = ManifestRepository(parts[0], parts[1], parts[2], parts[3])
        repos.append(r)
    return repos

def files_by_repo(repos):
    by_component = {}
    for repo_file in repos:
        comp = by_component.get(repo_file.component)
        if comp == None:
            by_component[repo_file.component] = [repo_file]
        else:
            comp.append(repo_file)
    return by_component

def repos_by_filename(repos):
    by_filename = {}
    for repo_file in repos:
        elem = by_filename.get(repo_file.releaseFile)
        if elem == None:
            by_filename[repo_file.releaseFile] = repo_file
        else:
            raise Exception(f"Multiple entries found for {repo_file.releaseFile}")
    return by_filename

def manifests_by_filename(manifests):
    by_file = {}
    for manifest in manifests:
        elem = by_file.get(manifest.fileName)
        if elem == None:
            by_file[manifest.fileName] = [manifest]
        else:
            elem.append(manifest)
    return by_file

def get_manifest_repos(pullsecret, releaseImage):
    result = subprocess.run(["oc", "adm", "release", "info", "--repos-with-manifests", "--registry-config", pullsecret, releaseImage], capture_output=True, universal_newlines=True)
    if result.returncode != 0:
        raise Exception(f"error running release command: {result.stderr}")
    return parse_manifest_repos_output(result.stdout)

def parse_manifest_output(result):
    manifests = []
    for line in result.splitlines():
        parts = line.split(" ")
        if len(parts) < 4:
            continue
        if len(parts) == 4:
            m = Manifest(parts[0], parts[1], parts[2], parts[3], "")
        else:
            m = Manifest(parts[0], parts[1], parts[2], parts[3], parts[4])
        manifests.append(m)
    return manifests

def get_needs_annotation(pullSpec, pullSecret):
    without = manifests_without_annotation(pullSpec, pullSecret, "include.release.openshift.io/ibm-cloud-managed")
    current_excludes = manifests_with_annotation(pullSpec, pullSecret, "exclude.release.openshift.io/internal-openshift-hosted")
    result = []
    for m in without:
        if not manifest_in_list(m, current_excludes):
            result.append(m)
    return result

def manifest_in_list(m, manifest_list):
    for x in manifest_list:
        if x.fileName == m.fileName and x.kind == m.kind and x.groupVersion == m.groupVersion and x.name == m.name and x.namespace == m.namespace:
            return True
    return False

def manifests_with_annotation(pullSpec, pullSecret, annotation):
    result = subprocess.run(["oc", "adm", "release", "info", "--includes-annotation", annotation, "--registry-config", pullSecret, pullSpec], capture_output=True, universal_newlines=True)
    if result.returncode != 0:
        raise Exception(f"error running release command: {result.stderr}")
    return parse_manifest_output(result.stdout)

def manifests_without_annotation(pullSpec, pullSecret, annotation):
    result = subprocess.run(["oc", "adm", "release", "info", "--omits-annotation", annotation, "--registry-config", pullSecret, pullSpec], capture_output=True, universal_newlines=True)
    if result.returncode != 0:
        raise Exception(f"error running release command: {result.stderr}")
    return parse_manifest_output(result.stdout)

def get_releasestream_pullspec(releaseStream):
    http = urllib3.PoolManager()
    url1 = f"https://openshift-release.svc.ci.openshift.org/api/v1/releasestream/{releaseStream}/latest"
    r = http.request('GET', url1)
    if r.status != 200:
        raise Exception(f"cannot retrieve latest release pull spec, status = {r.status}")
    data = json.loads(r.data)
    pullSpec = data["pullSpec"]
    if len(pullSpec) == 0:
        raise Exception("cannot get a valid pull spec")
    return pullSpec
