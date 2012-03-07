#!/bin/sh
#
# This file is part of `gitflow`.
# Copyright (c) 2012 Hartmut Goebel
# Distributed under a BSD-like license. For full terms see the file LICENSE.txt
#

basedir=$( readlink -fn $(dirname "$0" ))

gpgdir="$basedir"/gnupg
#export GNUPGHOME="$basedir"/gnupg
export GPG_AGENT_INFO=

mkdir -p "$gpgdir"
cd "$gpgdir"

LC_ALL=C gpg --gen-key --batch <<"EOF"
Key-Type: DSA
%no-ask-passphrase
%no-protection
%transient-key
Key-Length: 1024
Key-Usage: sign
Subkey-Type: ELG-E
Subkey-Length: 1024
Name-Real: Dummy Key for Gitflow testing
Expire-Date: 0
%pubring gitflow-test-dummy.pub
%secring gitflow-test-dummy.sec
%commit
%echo done
EOF

export GNUPGHOME="$basedir"/gnupg
LC_ALL=C gpg --import gitflow-test-dummy.sec gitflow-test-dummy.pub
