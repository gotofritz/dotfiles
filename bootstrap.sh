#!/usr/bin/env bash
# usage: ./bootstrap.sh [--force|-f] [--folders]
#   --force, -f  copy dotfiles into ~ without asking
#   --folders    also regenerate ~/.folder_aliases with gen_folder_aliases.py
cd "$(dirname "${BASH_SOURCE}")"

force=false
folders=false
for arg in "$@"; do
	case "$arg" in
		--force | -f) force=true ;;
		--folders) folders=true ;;
		*)
			echo "Unknown option: $arg" >&2
			echo "usage: $0 [--force|-f] [--folders]" >&2
			exit 1
			;;
	esac
done

git pull origin main
function doIt() {
	rsync --exclude ".git/" --exclude ".DS_Store" --exclude "bootstrap.sh" --exclude "setup-mac.sh" --exclude "Brewfile" \
		--exclude "README.md" --exclude "gen_folder_aliases.py" -av --no-perms . ~
	source ~/.bash_profile
}

if $force; then
	doIt
else
	read -p "This may overwrite existing files in your home directory. Are you sure? (y/n) " -n 1
	echo
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		doIt
	fi
fi
unset doIt

if $folders; then
	./gen_folder_aliases.py && source ~/.folder_aliases
fi
