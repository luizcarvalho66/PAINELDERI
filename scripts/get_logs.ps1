# Log Script for Databricks Apps
# Fetches the latest deployment/app logs

$CLI_PATH = "C:\Users\luicarvalho\AppData\Local\Microsoft\WinGet\Packages\Databricks.DatabricksCLI_Microsoft.Winget.Source_8wekyb3d8bbwe\databricks.exe"
$DB_PROFILE = "adb-7941093640821140"
$APP_NAME = "paineilri"

Write-Host "--- Fetching App Logs (last 100 lines) ---" -ForegroundColor Cyan
& $CLI_PATH apps logs $APP_NAME --tail-lines 100 --profile $DB_PROFILE
