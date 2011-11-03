# -*- coding: utf-8 -*-
require 'formula'

class GitFlowCompletion < Formula
  url 'https://github.com/iwata/git-flow-completion.git', :tag => '0.5.4.0'
  version '0.5.4.0'
  head 'https://github.com/iwata/git-flow-completion.git', :branch => 'develop'

  def initialize
    # We need to hard-code the formula name since Homebrew can't
    # deduce it from the formula's filename, and the git download
    # strategy really needs a valid name.

    super "git-flow-completion"
  end

  homepage 'https://github.com/iwata/git-flow-completion'
end

class GitFlow < Formula
  url 'https://github.com/iwata/gitflow.git', :tag => '0.5.14.0'
  version '0.5.14.0'
  head 'https://github.com/iwata/gitflow.git', :branch => 'develop'

  homepage 'https://github.com/iwata/gitflow'

  def patches
    DATA
  end

  def options
    [
        ['--bash-completion', "copy bash completion function file to #{prefix}/etc/bash_completion.d"],
        ['--zsh-completion', "copy zsh completion function file to #{share}/zsh/functions: please add #{share}/zsh/functions to $fpath in .zshrc"]
    ]
  end

  # for longopt
  depends_on 'gnu-getopt'

  def install
    system "make", "prefix=#{prefix}", "install"

    # Normally, etc files are installed directly into HOMEBREW_PREFIX,
    # rather than being linked from the Cellar — this is so that
    # configuration files don't get clobbered when you update.  The
    # bash-completion file isn't really configuration, though; it
    # should be updated when we upgrade the package.

    cellar_etc = prefix + 'etc'
    bash_completion_d = cellar_etc + "bash_completion.d"
    zsh_functions_d = share + 'zsh/functions'

    completion = GitFlowCompletion.new
    completion.brew do
      bash_completion_d.install "git-flow-completion.bash" if ARGV.include? '--bash-completion'
      zsh_functions_d.install "_git-flow" if ARGV.include? '--zsh-completion'
    end
  end
end

#This patch makes sure GNUtools are used on OSX.
#gnu-getopt is keg-only hence the backtick expansion.
#These aliases only exist for the duration of git-now,
#inside the git-flow shells. Normal operation of bash is
#unaffected - getopt will still find the version supplied
#by OSX in other shells, for example.
__END__
--- a/git-flow
+++ b/git-flow
@@ -37,6 +37,8 @@
 # policies, either expressed or implied, of Vincent Driessen.
 #
 
+alias getopt='`brew --prefix gnu-getopt`/bin/getopt'
+
 # enable debug mode
 if [ "$DEBUG" = "yes" ]; then
        set -x
