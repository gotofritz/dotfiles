export EDITOR=nano

if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
    color_prompt=yes
else
    color_prompt=
fi

if [ "$color_prompt" = yes ]; then
    export PS1="\n[\t] \[\e[01;33m\]\u@\H\[\e[0m\]:\$PWD\n"
    export SUDO_PS1="\n[\t] \[\e[33;01;41m\]\u@\H\[\e[0m\]:\$PWD\n"
else
    export PS1="\n[\t] \u@\H:\$PWD\n"
fi

unset color_prompt

# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    #alias dir='dir --color=auto'
    #alias vdir='vdir --color=auto'

    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# for ag
export LESS=-RFX

export PATH="$HOME/bin:$PATH"