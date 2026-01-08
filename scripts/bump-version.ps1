# PowerShell version bump script for Paracle

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('major', 'minor', 'patch')]
    [string]$BumpType = 'patch'
)

$ErrorActionPreference = "Stop"

# Colors
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Get current version
$pyprojectContent = Get-Content pyproject.toml -Raw
$currentVersion = [regex]::Match($pyprojectContent, 'version = "([^"]+)"').Groups[1].Value

Write-ColorOutput Yellow "Current version: $currentVersion"

# Parse version
$versionParts = $currentVersion -split '\.'
$major = [int]$versionParts[0]
$minor = [int]$versionParts[1]
$patch = [int]$versionParts[2]

# Determine new version
switch ($BumpType) {
    'major' {
        $newMajor = $major + 1
        $newVersion = "$newMajor.0.0"
    }
    'minor' {
        $newMinor = $minor + 1
        $newVersion = "$major.$newMinor.0"
    }
    'patch' {
        $newPatch = $patch + 1
        $newVersion = "$major.$minor.$newPatch"
    }
}

Write-ColorOutput Green "New version: $newVersion"

# Confirm
$confirmation = Read-Host "Proceed with version bump? (y/n)"
if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
    Write-ColorOutput Red "Aborted"
    exit 1
}

# Update pyproject.toml
Write-Host "Updating pyproject.toml..."
$pyprojectContent = $pyprojectContent -replace "version = `"$currentVersion`"", "version = `"$newVersion`""
$pyprojectContent | Set-Content pyproject.toml -NoNewline

# Update __version__ in main package
Write-Host "Updating package __version__..."
$initFile = "packages\paracle_core\__init__.py"
if (Test-Path $initFile) {
    $initContent = Get-Content $initFile -Raw
    $initContent = $initContent -replace "__version__ = `"$currentVersion`"", "__version__ = `"$newVersion`""
    $initContent | Set-Content $initFile -NoNewline
}

# Git operations
Write-Host "Creating git commit and tag..."
git add pyproject.toml packages\paracle_core\__init__.py
git commit -m "chore: bump version to $newVersion"
git tag -a "v$newVersion" -m "Release version $newVersion"

Write-ColorOutput Green "✅ Version bumped to $newVersion"
Write-ColorOutput Yellow "`nNext steps:"
Write-Host "  1. Review the changes: git show"
Write-Host "  2. Push to GitHub: git push origin develop && git push origin v$newVersion"
Write-Host "  3. GitHub Actions will automatically build and publish"
Write-Host ""
Write-ColorOutput Yellow "Or manually trigger workflow:"
Write-Host "  gh workflow run release.yml --ref v$newVersion"
