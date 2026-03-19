# Deploy Script for Databricks Apps
# Syncs local code to workspace and triggers deployment

# CLI: tenta env var, depois PATH do sistema
$CLI_PATH = if ($env:DATABRICKS_CLI_PATH) { $env:DATABRICKS_CLI_PATH } else { "databricks" }
$DB_PROFILE = "adb-7941093640821140"
$REMOTE_PATH = "/Workspace/Users/luiz.carvalho@edenred.com/paineilri"
$APP_NAME = "paineilri"

Write-Host "--- Syncing Source Code ---" -ForegroundColor Cyan
& $CLI_PATH sync . $REMOTE_PATH --watch=false --profile $DB_PROFILE

if ($LASTEXITCODE -eq 0) {
    Write-Host "--- Triggering App Deployment ---" -ForegroundColor Cyan
    & $CLI_PATH apps deploy $APP_NAME --source-code-path $REMOTE_PATH --profile $DB_PROFILE
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Deployment Process Started Successfully!" -ForegroundColor Green
        Write-Host "Monitor at: https://paineilri-7941093640821140.0.azure.databricksapps.com" -ForegroundColor Yellow
    }
    else {
        Write-Host "Deployment Trigger Failed!" -ForegroundColor Red
    }
}
else {
    Write-Host "Sync Failed, skipping deployment." -ForegroundColor Red
}
