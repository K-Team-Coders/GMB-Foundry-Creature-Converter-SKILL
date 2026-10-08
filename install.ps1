# GMB Foundry Creature Converter installer for Claude Code and Codex (Windows PowerShell)
#   irm https://raw.githubusercontent.com/GITHUB_USER/GMB-Foundry-Creature-Converter/main/install.ps1 | iex
$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$Repo = "GITHUB_USER/GMB-Foundry-Creature-Converter"
$Name = "gmb-foundry-creature-converter"
$Url  = "https://github.com/$Repo/releases/latest/download/$Name.zip"
$Tmp  = Join-Path $env:TEMP ("ff-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $Tmp | Out-Null
try {
    Write-Host "⬇  Скачиваю $Name…"
    Invoke-WebRequest -Uri $Url -OutFile "$Tmp\skill.zip" -UseBasicParsing
    Expand-Archive -Path "$Tmp\skill.zip" -DestinationPath "$Tmp\x" -Force
    $codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
    foreach ($root in @((Join-Path $HOME ".claude"), $codexHome)) {
        $dest = Join-Path $root "skills"
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        $target = Join-Path $dest $Name
        if (Test-Path $target) { Remove-Item -Recurse -Force $target }
        Copy-Item -Recurse "$Tmp\x\$Name" $target
        Write-Host "✓  Установлено: $target"
    }
    $b = "$Tmp\x\$Name\scripts"
    if ($Host.UI.SupportsVirtualTerminal -and -not $env:NO_COLOR -and (Test-Path "$b\banner.ansi")) {
        Write-Host ""; Write-Host (Get-Content -Raw -Encoding UTF8 "$b\banner.ansi")
    } elseif (Test-Path "$b\banner.txt") {
        Write-Host ""; Write-Host (Get-Content -Raw -Encoding UTF8 "$b\banner.txt")
    }
    $m = Join-Path $env:APPDATA $Name
    New-Item -ItemType Directory -Force -Path $m | Out-Null
    Set-Content -Path (Join-Path $m "welcome-shown") -Value "1"
    Write-Host "🎲 Готово. Перезапустите Claude Code / Codex. Geek Metaverse Bots: https://geek-metaverse-bots.ru · бот для D&D: https://t.me/GeekDungeonMasterBot"
} finally {
    Remove-Item -Recurse -Force $Tmp
}
