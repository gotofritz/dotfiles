dotfiles
========
"sensible hacker defaults for OS X"
Based on from https://github.com/mathiasbynens/dotfiles

- `./bootstrap.sh -f` copies the dotfiles into `~` and reloads the shell.
- `./setup-mac.sh` is a one-off setup for a new Mac: installs Homebrew and everything in `Brewfile`, links the starship config and sets macOS preferences. It is not loaded at shell startup.
- `Brewfile` lists the Homebrew packages. `brew bundle dump --describe --force --file=Brewfile` regenerates it from what's installed.
