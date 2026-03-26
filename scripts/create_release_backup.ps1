param(
    [string]$Version = "4.1",
    [string]$OutputName = "",
    [switch]$IncludeSensitiveAssets
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Test-ProjectPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    return Test-Path -LiteralPath $RelativePath
}

function Get-DefaultOutputName {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Version
    )

    $timestamp = Get-Date -Format "yyyyMMdd_HHmm"
    return "SysPragas_${Version}_backup_${timestamp}.zip"
}

function Get-BackupSources {
    param(
        [Parameter(Mandatory = $true)]
        [bool]$IncludeSensitive
    )

    $directories = @(
        "app",
        "assets",
        "docs",
        "modelo",
        "modelos",
        "scripts",
        "services",
        "tests"
    )

    $sensitiveDirectories = @(
        "assinaturas",
        "assinaturas_tecnicas",
        "certificado",
        "XSD"
    )

    if ($IncludeSensitive) {
        $directories += $sensitiveDirectories
    }

    $files = @(
        ".dockerignore",
        ".editorconfig",
        ".env.example",
        ".env.sefaz-homologacao.example",
        ".gitignore",
        "AGENTS.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "docker-compose.yml",
        "Dockerfile",
        "pyproject.toml",
        "README.md",
        "render.yaml",
        "SysPragas-Teste.spec",
        "VERSION"
    )

    return @{
        Directories = $directories
        SensitiveDirectories = $sensitiveDirectories
        Files = $files
    }
}

function Write-BackupLog {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Label,
        [Parameter(Mandatory = $true)]
        [string[]]$Items
    )

    Write-Output "$Label ($($Items.Count)):"
    foreach ($item in $Items) {
        Write-Output " - $item"
    }
}

function Get-BackupEntries {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Directories,
        [Parameter(Mandatory = $true)]
        [string[]]$Files
    )

    $entries = New-Object System.Collections.Generic.List[object]

    foreach ($directory in $Directories) {
        if (-not (Test-ProjectPath -RelativePath $directory)) {
            continue
        }

        $resolvedDirectory = (Resolve-Path -LiteralPath $directory).ProviderPath
        $prefixLength = $resolvedDirectory.Length + 1

        Get-ChildItem -LiteralPath $resolvedDirectory -Recurse -File | ForEach-Object {
            $fullName = $_.FullName
            $entryName = $directory + "/" + $fullName.Substring($prefixLength).Replace("\", "/")
            $entries.Add([pscustomobject]@{
                SourcePath = $fullName
                EntryName = $entryName
            })
        }
    }

    foreach ($file in $Files) {
        if (-not (Test-ProjectPath -RelativePath $file)) {
            continue
        }

        $resolvedFile = (Resolve-Path -LiteralPath $file).ProviderPath
        $entries.Add([pscustomobject]@{
            SourcePath = $resolvedFile
            EntryName = $file.Replace("\", "/")
        })
    }

    return $entries
}

function New-BackupArchive {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DestinationPath,
        [Parameter(Mandatory = $true)]
        [System.Collections.Generic.List[object]]$Entries
    )

    $fileStream = [System.IO.File]::Open($DestinationPath, [System.IO.FileMode]::Create)
    try {
        $archive = New-Object System.IO.Compression.ZipArchive($fileStream, [System.IO.Compression.ZipArchiveMode]::Create, $false)
        try {
            foreach ($entry in $Entries) {
                $archiveEntry = $archive.CreateEntry($entry.EntryName, [System.IO.Compression.CompressionLevel]::Optimal)
                $entryStream = $archiveEntry.Open()
                try {
                    $sourceStream = [System.IO.File]::OpenRead($entry.SourcePath)
                    try {
                        $sourceStream.CopyTo($entryStream)
                    }
                    finally {
                        $sourceStream.Dispose()
                    }
                }
                finally {
                    $entryStream.Dispose()
                }
            }
        }
        finally {
            $archive.Dispose()
        }
    }
    finally {
        $fileStream.Dispose()
    }
}

$releaseDir = Join-Path "release" ("SysPragas-" + $Version)
if (-not (Test-ProjectPath -RelativePath $releaseDir)) {
    throw "Release directory not found: $releaseDir"
}

if ([string]::IsNullOrWhiteSpace($OutputName)) {
    $OutputName = Get-DefaultOutputName -Version $Version
}

$outputPath = Join-Path $releaseDir $OutputName
if (Test-Path -LiteralPath $outputPath) {
    Remove-Item -LiteralPath $outputPath -Force
}

$sources = Get-BackupSources -IncludeSensitive:$IncludeSensitiveAssets.IsPresent
$entries = Get-BackupEntries -Directories $sources.Directories -Files $sources.Files

if ($entries.Count -eq 0) {
    throw "No files were selected for backup."
}

$includedItems = @($sources.Directories | ForEach-Object { "$_/" }) + $sources.Files
$includedItems = $includedItems | Where-Object { Test-ProjectPath -RelativePath $_.TrimEnd("/") }

$ignoredItems = @()
if (-not $IncludeSensitiveAssets.IsPresent) {
    $ignoredItems = $sources.SensitiveDirectories | Where-Object { Test-ProjectPath -RelativePath $_ } | ForEach-Object { "$_/" }
}

Write-Output "Backup mode: $(if ($IncludeSensitiveAssets.IsPresent) { 'including sensitive assets' } else { 'excluding sensitive assets' })"
Write-BackupLog -Label "Included items" -Items $includedItems
if ($ignoredItems.Count -gt 0) {
    Write-BackupLog -Label "Ignored sensitive items" -Items $ignoredItems
}
Write-Output "Included file entries: $($entries.Count)"

New-BackupArchive -DestinationPath $outputPath -Entries $entries

Write-Output "Backup created at $outputPath"
