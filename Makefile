#
# Copyright 2010 Vincent Driessen. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
# 
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY VINCENT DRIESSEN ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL VINCENT DRIESSEN OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# 
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of Vincent Driessen.
#

SHELL = /bin/sh
srcdir = .

prefix=/usr/local

# files that need mode 755
EXEC_FILES=git-flow

# files that need mode 644
SCRIPT_FILES =git-flow-init
SCRIPT_FILES+=git-flow-feature
SCRIPT_FILES+=git-flow-hotfix
SCRIPT_FILES+=git-flow-release
SCRIPT_FILES+=git-flow-support
SCRIPT_FILES+=git-flow-version
SCRIPT_FILES+=gitflow-common
SCRIPT_FILES+=gitflow-shFlags

all:
	@echo "usage: make install"
	@echo "       make uninstall"

install:
	@test -f gitflow-shFlags || (echo "Run 'git submodule init && git submodule update' first." ; exit 1 )
	install -d -m 0755 $(prefix)/bin
	install -m 0755 $(EXEC_FILES) $(prefix)/bin
	install -m 0644 $(SCRIPT_FILES) $(prefix)/bin

uninstall:
	test -d $(prefix)/bin && \
	cd $(prefix)/bin && \
	rm -f $(EXEC_FILES) $(SCRIPT_FILES)

$(srcdir)/contrib/gitflow-installer.shar:
	@test -f $(srcdir)/gitflow-shFlags || { echo "Run 'git submodule init && git submodule update' first." >&2; exit 1; }
	echo "#!/bin/sh" > $@
	find $(srcdir) -mindepth 1 -maxdepth 2 -not -path '*/.git*' \
	       -not -path '*/contrib/*' -not -path '*/shFlags/*' \
	       -not -type d | xargs -n100 shar >> $@
	 chmod +x $@

clean-shar:
	@rm -f $(srcdir)/contrib/gitflow-installer.shar
	@rm -f $(srcdir)/contrib/gitflow-installer.shar.*

shar: clean-shar $(srcdir)/contrib/gitflow-installer.shar

gpg: $(srcdir)/contrib/gitflow-installer.shar
	@if gpg --verify $^ >/dev/null 2>&1; then \
	  echo "$^: Already signed." >&2; \
	  exit 1; \
	fi
	@cat $^ | sed -E '\@^#!/bin/(ba|c|tc|z|k)?sh@d' > $^.temp
	@rm $^
	@echo "#!/bin/sh" > $^
	@echo "_ignore_pgp=<<'Hash: SHA1'" >> $^ 
	gpg -a --sign -o $^.asc --clearsign $^.temp
	@cat $^.asc >> $^
	@rm -f $^.*
	@chmod +x $^

sign: gpg

pgp: gpg

signed-shar: clean-shar gpg

.PHONY: signed-shar sign pgp gpg shar clean-shar
