# Older container shells must not reset the shared fish 4.3 migration state.
if string match -qr "^[123][.]|^4[.][012][.]" -- $version
    if set -q __fish_initialized
        set -g __fish_initialized $__fish_initialized
    end
    if not set -q fish_key_bindings
        set -g fish_key_bindings fish_default_key_bindings
    else
        set -g fish_key_bindings $fish_key_bindings
    end
end

if test -f /usr/share/cachyos-fish-config/cachyos-config.fish
    source /usr/share/cachyos-fish-config/cachyos-config.fish
end

# overwrite greeting
# potentially disabling fastfetch
#function fish_greeting
#    # smth smth
#end
set -gx PATH ~/.npm-global/bin $PATH

# uv
if functions -q fish_add_path
    fish_add_path "$HOME/.local/bin"
else if not contains -- "$HOME/.local/bin" $PATH
    set -gx PATH "$HOME/.local/bin" $PATH
end

if test -f ~/.config/fish/secrets.fish
    source ~/.config/fish/secrets.fish
end
