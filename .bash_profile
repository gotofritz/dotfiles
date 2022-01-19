# Add `~/bin` to the `$PATH`
export PATH="$HOME/bin:$PATH"

# Load the shell dotfiles, and then some:
# * ~/.path can be used to extend `$PATH`.
# * ~/.extra can be used for other settings you don’t want to commit.
for file in ~/.{path,git-prompt.sh,bash_prompt,exports,aliases,functions,extra,backup}; do
    [ -r "$file" ] && [ -f "$file" ] && source "$file"
done
unset file

# Suppressing "The default interactive shell is now zsh" message
export BASH_SILENCE_DEPRECATION_WARNING=1

# Case-insensitive globbing (used in pathname expansion)
shopt -s nocaseglob

# Append to the Bash history file, rather than overwriting it
shopt -s histappend
# timestamps for later analysis. www.debian-administration.org/users/rossen/weblog/1
export HISTTIMEFORMAT='%F %T '
# keep history up to date, across sessions, in realtime
#  http://unix.stackexchange.com/a/48113
#   - ignorespace = don't save lines that begin with a space
#   - ignoredups  = don't save duplicate lines
#   - erasedups   = erase across sessions
export HISTCONTROL=ignorespace:ignoredups:erasedups
# big big history (default is 500)
export HISTSIZE=100000
export HISTFILESIZE=$HISTSIZE

# Autocorrect typos in path names when using `cd`
shopt -s cdspell

# Enable some Bash 4 features when possible:
# * `autocd`, e.g. `**/qux` will enter `./foo/bar/baz/qux`
# * Recursive globbing, e.g. `echo **/*.txt`
for option in autocd globstar; do
    shopt -s "$option" 2> /dev/null
done

# Add tab completion for SSH hostnames based on ~/.ssh/config, ignoring wildcards
[ -e "$HOME/.ssh/config" ] && complete -o "default" -o "nospace" -W "$(grep "^Host" ~/.ssh/config | grep -v "[?*]" | cut -d " " -f2 | tr ' ' '\n')" scp sftp ssh

# Add tab completion for `defaults read|write NSGlobalDomain`
# You could just use `-g` instead, but I like being explicit
complete -W "NSGlobalDomain" defaults

# Add `killall` tab completion for common apps
complete -o "nospace" -W "Contacts Calendar Dock Finder Mail Safari iTunes SystemUIServer Terminal Twitter" killall

# If possible, add tab completion for many more commands
[ -f /etc/bash_completion ] && source /etc/bash_completion

# Set up rbenv for Homebrew. Make sure path is BEFORE Homebrew's /usr/local/[s]bin
# To enable shims and autocompletion add to your profile:
if which rbenv > /dev/null; then eval "$(rbenv init -)"; fi

if which pyenv > /dev/null; then eval "$(pyenv init -)"; fi

