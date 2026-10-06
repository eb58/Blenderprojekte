$projectRoot = Split-Path (Split-Path $PSScriptRoot)
$libraryRoot = Join-Path $projectRoot 'assets\library'
foreach ($assetId in @('painted_wooden_bench', 'modular_street_seating', 'bar_chair_round_01', 'tree_small_02')) {
    $assetFolder = Join-Path $libraryRoot $assetId
    New-Item -ItemType Directory -Force -Path $assetFolder | Out-Null
    $files = Invoke-RestMethod "https://api.polyhaven.com/files/$assetId"
    $model = $files.blend.'1k'.blend
    $downloads = @(@{Path = "$assetId.blend"; Info = $model})
    foreach ($entry in $model.include.PSObject.Properties) {
        $downloads += @{Path = $entry.Name; Info = $entry.Value}
    }
    foreach ($download in $downloads) {
        $destination = Join-Path $assetFolder $download.Path
        New-Item -ItemType Directory -Force -Path (Split-Path $destination) | Out-Null
        if (-not (Test-Path -LiteralPath $destination)) {
            Invoke-WebRequest -UseBasicParsing -Uri $download.Info.url -OutFile $destination
        }
        $hash = (Get-FileHash -LiteralPath $destination -Algorithm MD5).Hash
        if ($hash -ne $download.Info.md5) { throw "Prüfsumme stimmt nicht: $destination" }
    }
    Write-Output "Heruntergeladen und geprüft: $assetId"
}
