AUTO_DETECTED_GIT_EXEC_PATH := $(shell git --exec-path 2>/dev/null || echo /usr/libexec/git-core)
GIT_EXEC_PATH=$(AUTO_DETECTED_GIT_EXEC_PATH)

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
	install -d -m 0755 $(GIT_EXEC_PATH)
	install -m 0755 $(EXEC_FILES) $(GIT_EXEC_PATH)
	install -m 0644 $(SCRIPT_FILES) $(GIT_EXEC_PATH)

uninstall:
	test -d $(GIT_EXEC_PATH) && \
	cd $(GIT_EXEC_PATH) && \
	rm -f $(EXEC_FILES) $(SCRIPT_FILES)
