GIT_EXEC_PATH=/usr/libexec/git-core

install:
	install -m 0755 -t $(GIT_EXEC_PATH) git-flow
	install -m 0644 -t $(GIT_EXEC_PATH) \
		git-flow-feature \
		git-flow-hotfix \
		git-flow-release \
		git-flow-support \
		git-flow-version

