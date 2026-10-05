$studioPython = 'C:\Program Files\Blender Foundation\Blender 5.2\5.2\python\bin\python.exe'
if (-not (Test-Path -LiteralPath $studioPython)) { throw 'Blenders Python wurde nicht gefunden.' }
$studioScript = Join-Path $PSScriptRoot 'museum_studio.py'
$studioUrl = 'http://127.0.0.1:8765'
try {
    $null = Invoke-WebRequest -Uri "$studioUrl/api/status" -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop
} catch {
    Start-Process -FilePath $studioPython -ArgumentList ('-B "' + $studioScript + '"') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        try { $null = Invoke-WebRequest -Uri "$studioUrl/api/status" -UseBasicParsing -TimeoutSec 1 -ErrorAction Stop; break }
        catch { Start-Sleep -Milliseconds 250 }
    }
}
Start-Process $studioUrl
