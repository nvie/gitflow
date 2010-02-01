GIT_EXEC_PATH=`git --exec-path 2>/dev/null || echo /usr/libexec/git-core`

all:
	@echo "usage: make install"
	@echo "       make uninstall"

install:
	# TODO: Add installation of shFlags to this file too
	install -d -m 0755 $(GIT_EXEC_PATH)
	install -m 0755 git-flow $(GIT_EXEC_PATH)
	install -m 0644 \
		git-flow-feature \
		git-flow-hotfix \
		git-flow-release \
		git-flow-support \
		git-flow-version \
		$(GIT_EXEC_PATH)

uninstall:
	test -d $(GIT_EXEC_PATH) && rm -f $(GIT_EXEC_PATH)/git-flow*
