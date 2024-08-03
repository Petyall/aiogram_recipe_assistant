#!/bin/bash

black "$1"
isort "$1"
flake8 "$1"