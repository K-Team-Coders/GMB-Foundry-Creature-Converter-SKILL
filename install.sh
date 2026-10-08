#!/usr/bin/env sh
# GMB Foundry Creature Converter installer for Claude Code and Codex (macOS / Linux / WSL)
#   curl -fsSL https://raw.githubusercontent.com/GITHUB_USER/GMB-Foundry-Creature-Converter/main/install.sh | sh
# Options (env): TARGET=claude|codex|all (default: all)   VERSION=latest|v1.0.0
set -eu
REPO="GITHUB_USER/GMB-Foundry-Creature-Converter"
NAME="gmb-foundry-creature-converter"
VERSION="${VERSION:-latest}"
TARGET="${TARGET:-all}"

if [ "$VERSION" = "latest" ]; then
  URL="https://github.com/$REPO/releases/latest/download/$NAME.zip"
else
  URL="https://github.com/$REPO/releases/download/$VERSION/$NAME.zip"
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
echo "⬇  Скачиваю $NAME ($VERSION)…"
if command -v curl >/dev/null 2>&1; then curl -fsSL "$URL" -o "$TMP/skill.zip"
else wget -qO "$TMP/skill.zip" "$URL"; fi

if command -v unzip >/dev/null 2>&1; then unzip -q "$TMP/skill.zip" -d "$TMP/x"
else python3 -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$TMP/skill.zip" "$TMP/x"; fi

install_to() {
  dest="$1/skills"
  mkdir -p "$dest"
  rm -rf "$dest/$NAME"
  cp -R "$TMP/x/$NAME" "$dest/$NAME"
  echo "✓  Установлено: $dest/$NAME"
}
case "$TARGET" in
  claude) install_to "$HOME/.claude" ;;
  codex)  install_to "${CODEX_HOME:-$HOME/.codex}" ;;
  all)    install_to "$HOME/.claude"; install_to "${CODEX_HOME:-$HOME/.codex}" ;;
  *) echo "TARGET должен быть claude, codex или all"; exit 1 ;;
esac
# welcome banner (and mark it as shown so the scripts don't repeat it)
B="$TMP/x/$NAME/scripts"
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ -f "$B/banner.ansi" ]; then echo; cat "$B/banner.ansi"; echo
elif [ -f "$B/banner.txt" ]; then echo; cat "$B/banner.txt"; echo; fi
M="${XDG_CONFIG_HOME:-$HOME/.config}/$NAME"
mkdir -p "$M" 2>/dev/null && : > "$M/welcome-shown" 2>/dev/null || true
echo "🎲 Готово. Перезапустите Claude Code / Codex и попросите: «перегони статблок в Foundry»."
echo "   Geek Metaverse Bots: https://geek-metaverse-bots.ru · бот для D&D: https://t.me/GeekDungeonMasterBot"
