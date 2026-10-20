#!/bin/bash

DOCKER_IMAGE="ghcr.io/fmatthies/snomed-annotation-audit/audit-image"
CURRENT_VERSION="1.0.0"

if [[ ! -d ./data ]]; then
  echo "This script requires a './data' folder to mount into the Docker container."
  echo "Store the INCEpTION project ZIP and policy HDF5 file there."
  exit 1
fi

if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <INCEpTION-project.zip> [image-version] [policy-file.hdf5]"
  echo "The image version defaults to ${CURRENT_VERSION}."
  echo "If the policy file is omitted, ./data must contain exactly one .hdf5 or .h5 file."
  exit 0
fi

VERSION=${2:-$CURRENT_VERSION}

ZIP=$1
if [[ "${ZIP: -4}" != ".zip" ]]; then
  ZIP="$1.zip"
fi
ZIP=$(basename "${ZIP}")

if [[ ! -f "./data/${ZIP}" ]]; then
  echo "INCEpTION project ZIP not found: ./data/${ZIP}"
  exit 1
fi

if [[ -n "$3" ]]; then
  POLICY=$(basename "$3")
  if [[ ! -f "./data/${POLICY}" ]]; then
    echo "Policy HDF5 file not found: ./data/${POLICY}"
    exit 1
  fi
else
  shopt -s nullglob
  POLICY_FILES=(./data/*.hdf5 ./data/*.h5)
  shopt -u nullglob
  if [[ ${#POLICY_FILES[@]} -ne 1 ]]; then
    echo "Expected exactly one policy HDF5 file in ./data; found ${#POLICY_FILES[@]}."
    echo "Specify one explicitly as the third argument."
    exit 1
  fi
  POLICY=$(basename "${POLICY_FILES[0]}")
fi

docker run \
  --volume ./data:/app/data \
  --rm \
  "${DOCKER_IMAGE}":"${VERSION}" \
  log-critical-documents \
  --lists-path "/app/data/${POLICY}" \
  "/app/data/${ZIP}"
