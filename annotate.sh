FILE="${1}"
if [[ -z "${FILE}" ]]; then
  echo "Must specify a file to annotate"
  exit 1
fi

## Change this to your annotation
PROFILE_ANNOTATION="include.release.openshift.io/ibm-cloud-managed"

manifest-annotator "${FILE}" "${PROFILE_ANNOTATION}" "true"
