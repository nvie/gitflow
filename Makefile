GIT_EXEC_PATH=`git --exec-path 2>/dev/null || echo /usr/libexec/git-core`

all:
	@echo "There is only one target here: install"
	@echo "This message is deliberately inserted here to prevent accidental installation."
	@echo ""
	@echo "Use 'make install' explicitly to install git-flow."

install:
	install -d -m 0755 $(GIT_EXEC_PATH)
	install -m 0755 git-flow $(GIT_EXEC_PATH)
	install -m 0644 \
		git-flow-feature \
		git-flow-hotfix \
		git-flow-release \
		git-flow-support \
		git-flow-version \
		$(GIT_EXEC_PATH)

