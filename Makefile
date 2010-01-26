GIT_EXEC_PATH=/usr/libexec/git-core

all:
	@echo "There is only one target here: install"
	@echo "This message is deliberately inserted here to prevent accidental installation."
	@echo ""
	@echo "Use 'make install' explicitly to install git-flow."

install:
	install -m 0755 -t $(GIT_EXEC_PATH) git-flow
	install -m 0644 -t $(GIT_EXEC_PATH) \
		git-flow-feature \
		git-flow-hotfix \
		git-flow-release \
		git-flow-support \
		git-flow-version

