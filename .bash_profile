# Load the shell dotfiles:
# * ~/.path sets up Homebrew and extends `$PATH` (load it first).
# * ~/.extra can be used for other settings you don’t want to commit.
for file in ~/.{path,exports,aliases,functions,extra,bash_prompt}; do
  [ -r "$file" ] && [ -f "$file" ] && source "$file"
done
unset file

# Suppress the "default interactive shell is now zsh" message
export BASH_SILENCE_DEPRECATION_WARNING=1

# Case-insensitive globbing (used in pathname expansion)
shopt -s nocaseglob
# Append to the Bash history file, rather than overwriting it
shopt -s histappend
# Re-check the window size after each command, so long lines wrap correctly
shopt -s checkwinsize
# Autocorrect typos in path names when using `cd`
shopt -s cdspell

# Bash 4+ only (Homebrew's bash, not the 3.2 that macOS ships):
# * `autocd`, e.g. `**/qux` will enter `./foo/bar/baz/qux`
# * `globstar`, recursive globbing, e.g. `echo **/*.txt`
# * `dirspell`, autocorrect directory names during tab completion
for option in autocd globstar dirspell; do
  shopt -s "$option" 2> /dev/null
done

# Tab completion: Homebrew's bash-completion@2 (also completes git, gh, brew…),
# falling back to the system one
if [ -r "$HOMEBREW_PREFIX/etc/profile.d/bash_completion.sh" ]; then
  source "$HOMEBREW_PREFIX/etc/profile.d/bash_completion.sh"
elif [ -f /etc/bash_completion ]; then
  source /etc/bash_completion
fi

# Tab completion for SSH hostnames based on ~/.ssh/config, ignoring wildcards
[ -e "$HOME/.ssh/config" ] && complete -o "default" -o "nospace" -W "$(grep "^Host" ~/.ssh/config | grep -v "[?*]" | cut -d " " -f2- | tr ' ' '\n')" scp sftp ssh

# fzf key bindings: Ctrl-R history search, Ctrl-T file picker, Alt-C cd
command -v fzf > /dev/null && eval "$(fzf --bash 2> /dev/null)"
