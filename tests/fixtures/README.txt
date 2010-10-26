These are the available fixtures:

custom_repo
------------------

- Config:
     core.repositoryformatversion=0
     core.filemode=true
     core.bare=false
     core.logallrefupdates=true
     core.ignorecase=true
     gitflow.branch.master=production
     gitflow.branch.develop=master
     gitflow.prefix.feature=f-
     gitflow.prefix.release=rel-
     gitflow.prefix.hotfix=hf-
     gitflow.prefix.support=supp-
     gitflow.prefix.versiontag=v
     foo.bar=qux

- Status:
     # On branch master
     nothing to commit (working directory clean)

- Branches:
     * master
       production

- Commit graph:
     * 84f686f (HEAD, production, master) Initial commit


dirty_sample_repo
------------------

- Config:
     core.repositoryformatversion=0
     core.filemode=true
     core.bare=false
     core.logallrefupdates=true
     core.ignorecase=true
     gitflow.branch.master=master
     gitflow.branch.develop=develop
     gitflow.prefix.feature=feature/
     gitflow.prefix.release=release/
     gitflow.prefix.hotfix=hotfix/
     gitflow.prefix.support=support/
     gitflow.prefix.versiontag=

- Status:
     # On branch feature/recursion
     # Changes to be committed:
     #   (use "git reset HEAD <file>..." to unstage)
     #
     #	modified:   odd.py
     #
     # Changed but not updated:
     #   (use "git add <file>..." to update what will be committed)
     #   (use "git checkout -- <file>..." to discard changes in working directory)
     #
     #	modified:   README.txt
     #

- Branches:
       develop
       feature/even
     * feature/recursion
       master

- Commit graph:
     * 54d59c8 (HEAD, feature/recursion) Made the definition of odd recursive.
     | * e56be18 (feature/even) Rename file, to match both functions.
     | * 2ca717f Add even function.
     |/  
     * 2b34cd2 (develop) Add naive initial implementation of the odd function.
     * c8b6dea Describe intentions.
     * 84b34bc Add README file.
     * 296586b (master) Initial commit


partly_inited
------------------

- Config:
     core.repositoryformatversion=0
     core.filemode=true
     core.bare=false
     core.logallrefupdates=true
     core.ignorecase=true
     gitflow.branch.master=production
     gitflow.prefix.feature=f-
     foo.bar=qux

- Status:
     # On branch master
     nothing to commit (working directory clean)

- Branches:
     * master
       production

- Commit graph:
     * 84f686f (HEAD, production, master) Initial commit


sample_repo
------------------

- Config:
     core.repositoryformatversion=0
     core.filemode=true
     core.bare=false
     core.logallrefupdates=true
     core.ignorecase=true
     gitflow.branch.master=master
     gitflow.branch.develop=develop
     gitflow.prefix.feature=feature/
     gitflow.prefix.release=release/
     gitflow.prefix.hotfix=hotfix/
     gitflow.prefix.support=support/
     gitflow.prefix.versiontag=

- Status:
     # On branch feature/recursion
     nothing to commit (working directory clean)

- Branches:
       develop
       feature/even
     * feature/recursion
       master

- Commit graph:
     * 54d59c8 (HEAD, feature/recursion) Made the definition of odd recursive.
     | * e56be18 (feature/even) Rename file, to match both functions.
     | * 2ca717f Add even function.
     |/  
     * 2b34cd2 (develop) Add naive initial implementation of the odd function.
     * c8b6dea Describe intentions.
     * 84b34bc Add README file.
     * 296586b (master) Initial commit


