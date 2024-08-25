#!/bin/zsh

ROOT_DIR="$(git rev-parse --show-toplevel)"

pytest "$ROOT_DIR/tests"
