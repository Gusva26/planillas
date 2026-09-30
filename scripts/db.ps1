param([ValidateSet('init','up','status','stop')][string]$Action = 'status')
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
Push-Location $taskRoot
try {
    if ($Action -eq 'init') {
        if (-not (Test-Path -LiteralPath '.env')) {
            $taskBytes = New-Object byte[] 32
            $taskRng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
            try { $taskRng.GetBytes($taskBytes) } finally { $taskRng.Dispose() }
            $taskSecret = [Convert]::ToHexString($taskBytes).ToLowerInvariant()
            [IO.File]::WriteAllText((Join-Path $taskRoot '.env'), "POSTGRES_PASSWORD=$taskSecret`nPOSTGRES_PORT=55432`n")
            Write-Output 'Configuración local creada. La contraseña no se muestra y .env se excluye de Git.'
        } else { Write-Output '.env existente conservado.' }
    } elseif ($Action -eq 'up') {
        docker compose up -d --wait --wait-timeout 60 db
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo iniciar PostgreSQL.' }
    } elseif ($Action -eq 'stop') {
        docker compose stop db
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo detener PostgreSQL.' }
    } else {
        docker compose ps
        if ($LASTEXITCODE -ne 0) { throw 'No se pudo consultar PostgreSQL.' }
    }
} finally { Pop-Location }
