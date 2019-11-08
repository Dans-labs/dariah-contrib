#!/bin/sh

cd /opt/web-apps

# on linux
date +%s | sha256sum | base64 | head -c 32 > dariah_jwt.secret

# on mac
# date +%s | shasum -a 256 | base64 | head -c 32 > dariah_jwt.secret
