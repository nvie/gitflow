GIT_EXEC_PATH=`git --exec-path 2>/dev/null || echo /usr/libexec/git-core`

# files that need mode 755
EXEC_FILES=git-flow

# files that need mode 644
SCRIPT_FILES =git-flow-init
SCRIPT_FILES+=git-flow-feature
SCRIPT_FILES+=git-flow-hotfix
SCRIPT_FILES+=git-flow-release
SCRIPT_FILES+=git-flow-support
SCRIPT_FILES+=git-flow-version
SCRIPT_FILES+=shFlags.sh

all:
	@echo "usage: make install"
	@echo "       make uninstall"

install:
	install -d -m 0755 $(GIT_EXEC_PATH)
	install -m 0755 $(EXEC_FILES) $(GIT_EXEC_PATH)
	install -m 0644 $(SCRIPT_FILES) $(GIT_EXEC_PATH)

uninstall:
	test -d $(GIT_EXEC_PATH) && \
	cd $(GIT_EXEC_PATH) && \
	rm -f $(EXEC_FILES) $(SCRIPT_FILES)
