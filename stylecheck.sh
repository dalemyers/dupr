#!/bin/bash

pushd "${VIRTUAL_ENV}/.." > /dev/null

python -m black --line-length 100 dupr tests
python -m pylint --rcfile=pylintrc dupr tests
python -m mypy --ignore-missing-imports dupr/ tests/

popd > /dev/null