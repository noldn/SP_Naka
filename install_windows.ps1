$ErrorActionPreference = "Stop"
$RepositoryUrl = "https://github.com/noldn/SP_Naka.git"
$Target = Join-Path $env:USERPROFILE "Documents\SP_Naka"
$ScriptRootProject = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Desktop fehlt. Bitte zuerst Docker Desktop installieren."
    Write-Host "https://www.docker.com/products/docker-desktop/"
    Read-Host "Eingabetaste zum Beenden"
    exit 1
}

if (Test-Path (Join-Path $ScriptRootProject "compose.yaml")) {
    $Project = $ScriptRootProject
} elseif (Test-Path (Join-Path $Target ".git")) {
    $Project = $Target
    $Changes = git -C $Project status --porcelain
    if (-not $Changes) { git -C $Project pull --ff-only }
    else { Write-Host "Lokale Änderungen gefunden; keine automatische Aktualisierung." }
} else {
    git clone $RepositoryUrl $Target
    $Project = $Target
}

New-Item -ItemType Directory -Force -Path (Join-Path $Project "data\local") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Project "output") | Out-Null
docker compose -f (Join-Path $Project "compose.yaml") build

$Desktop = [Environment]::GetFolderPath("Desktop")
$StartFile = Join-Path $Desktop "SP_Naka starten.cmd"
$StopFile = Join-Path $Desktop "SP_Naka stoppen.cmd"
"@echo off`r`ncd /d `"$Project`"`r`ndocker compose up -d --build`r`nstart http://localhost:8765`r`n" | Set-Content -Encoding ASCII $StartFile
"@echo off`r`ncd /d `"$Project`"`r`ndocker compose down`r`n" | Set-Content -Encoding ASCII $StopFile

Write-Host "Installation abgeschlossen. Desktop-Verknüpfungen wurden erstellt."
Read-Host "Eingabetaste zum Beenden"
