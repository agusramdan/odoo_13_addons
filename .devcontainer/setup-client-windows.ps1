#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Setup Laptop FDE (Windows): DevPod + SSH Agent + LiteLLM " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# --- 1. Input Interaktif ---
$VpsHost = Read-Host "Masukkan SSH Host VPS (contoh: dev@103.x.x.x)"
if ([string]::IsNullOrWhiteSpace($VpsHost)) {
    Write-Error "SSH Host VPS wajib diisi."
    exit 1
}

$DefaultUser = $env:USERNAME
$DevUser = Read-Host "Masukkan nama developer (untuk volume memori Hermes) [$DefaultUser]"
if ([string]::IsNullOrWhiteSpace($DevUser)) { $DevUser = $DefaultUser }

$LiteLlmKey = Read-Host "Masukkan LiteLLM Virtual Key Anda"

# --- 2. Install DevPod CLI ---
Write-Host "`n[1/5] Memeriksa & menginstal DevPod CLI..." -ForegroundColor Yellow
if (-not (Get-Command devpod -ErrorAction SilentlyContinue)) {
    $InstallDir = "$Env:APPDATA\devpod"
    New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]'Tls12'
    Invoke-WebRequest -Uri "https://github.com/loft-sh/devpod/releases/latest/download/devpod-windows-amd64.exe" -OutFile "$InstallDir\devpod.exe"

    # Tambahkan ke User PATH tanpa menduplikasi System PATH
    $UserPath = [Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::User)
    if ($UserPath -notlike "*$InstallDir*") {
        $NewUserPath = if ([string]::IsNullOrWhiteSpace($UserPath)) { $InstallDir } else { "$UserPath;$InstallDir" }
        [Environment]::SetEnvironmentVariable("Path", $NewUserPath, [System.EnvironmentVariableTarget]::User)
    }
    $env:Path += ";$InstallDir"

    Write-Host "-> DevPod CLI berhasil diinstal di $InstallDir." -ForegroundColor Green
} else {
    Write-Host "-> DevPod CLI sudah terinstal." -ForegroundColor Green
}

# --- 3. Aktifkan Windows OpenSSH Agent Service ---
Write-Host "`n[2/5] Mengaktifkan Windows OpenSSH Authentication Agent..." -ForegroundColor Yellow
Set-Service -Name ssh-agent -StartupType Automatic
Start-Service ssh-agent
Write-Host "-> Service ssh-agent aktif (Automatic)." -ForegroundColor Green

# --- 4. Cek / Generate SSH Key & Tambahkan ke Agent ---
Write-Host "`n[3/5] Memeriksa SSH Key..." -ForegroundColor Yellow
$SshDir = "$env:USERPROFILE\.ssh"
$SshKey = "$SshDir\id_ed25519"

if (-not (Test-Path $SshKey)) {
    New-Item -ItemType Directory -Force -Path $SshDir | Out-Null
    ssh-keygen -t ed25519 -f $SshKey -N '""' -C "$DevUser@fde-windows"
    Write-Host "`n-> Public Key Anda (salin ke GitHub & ~/.ssh/authorized_keys di VPS):" -ForegroundColor Cyan
    Get-Content "$SshKey.pub"
    Write-Host ""
} else {
    Write-Host "-> SSH Key ditemukan di $SshKey." -ForegroundColor Green
}

ssh-add $SshKey

# --- 5. Simpan Environment Variables (User Scope) ---
Write-Host "`n[4/5] Menyimpan Environment Variables (DEV_USER & LITELLM_VIRTUAL_KEY)..." -ForegroundColor Yellow
[Environment]::SetEnvironmentVariable("DEV_USER", $DevUser, "User")
[Environment]::SetEnvironmentVariable("LITELLM_VIRTUAL_KEY", $LiteLlmKey, "User")
$env:DEV_USER = $DevUser
$env:LITELLM_VIRTUAL_KEY = $LiteLlmKey
Write-Host "-> Environment Variables tersimpan permanen." -ForegroundColor Green

# --- 6. Konfigurasi DevPod Provider & IDE ---
Write-Host "`n[5/5] Mengonfigurasi DevPod SSH Provider ($VpsHost)..." -ForegroundColor Yellow
# Refresh PATH sementara jika baru install lewat winget
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

try { devpod provider delete ssh 2>$null } catch {}
devpod provider add ssh -o HOST=$VpsHost
devpod provider use ssh
devpod ide use vscode

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  SETUP LAPTOP WINDOWS SELESAI!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Tutup & buka ulang PowerShell/Terminal baru, lalu tes dengan:"
Write-Host "  devpod up git@github.com:org/repo-odoo.git@main --id test-01"
