#!/bin/bash
pushd iris/data
protoc --python_out=. *.proto
popd
