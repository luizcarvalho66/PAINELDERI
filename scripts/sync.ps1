# Sync Script for Databricks Apps
# Synchronizes local source code to the Databricks Workspace

$CLI_PATH = "C:\Users\luicarvalho\AppData\Local\Microsoft\WinGet\Packages\Databricks.DatabricksCLI_Microsoft.Winget.Source_8wekyb3d8bbwe\databricks.exe"
$DB_PROFILE = "adb-7941093640821140"
$REMOTE_PATH = "/Workspace/Users/luiz.carvalho@edenred.com/painelri"

Write-Host "--- Syncing Local Files to Databricks Workspace ---" -ForegroundColor Cyan
& $CLI_PATH sync . $REMOTE_PATH --watch=false --profile $DB_PROFILE

if ($LASTEXITCODE -eq 0) {
    Write-Host "Sync Completed Successfully!" -ForegroundColor Green
}
else {
    Write-Host "Sync Failed with exit code $LASTEXITCODE" -ForegroundColor Red
}
