$urls = @(
    @{ Name = "Login"; Url = "https://sccp-prepublish.onrender.com/login"; Method = "GET" },
    @{ Name = "Validador (No Auth)"; Url = "https://sccp-prepublish.onrender.com/validador"; Method = "HEAD" },
    @{ Name = "Tablero Operador (No Auth)"; Url = "https://sccp-prepublish.onrender.com/tablero/operador"; Method = "HEAD" },
    @{ Name = "Legacy Root"; Url = "https://auditoria-postenvio.onrender.com/"; Method = "HEAD" },
    @{ Name = "Legacy Insolation Check"; Url = "https://auditoria-postenvio.onrender.com/tablero/operador"; Method = "HEAD" }
)

$results = @()

foreach ($u in $urls) {
    $resObj = @{
        Name = $u.Name
        Url = $u.Url
        Method = $u.Method
        Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        StatusCode = $null
        StatusDescription = $null
        ContentLength = 0
        RedirectLocation = $null
        BodyHashSHA256 = $null
    }

    try {
        if ($u.Method -eq "GET") {
            $r = Invoke-WebRequest -Uri $u.Url -Method Get -UseBasicParsing -ErrorAction Stop
            $resObj.StatusCode = [int]$r.StatusCode
            $resObj.StatusDescription = $r.StatusDescription
            $resObj.ContentLength = $r.RawContentLength
            if ($r.Content) {
                $resObj.ContentLength = $r.Content.Length
                $sha = [System.Security.Cryptography.SHA256]::Create()
                $bytes = [System.Text.Encoding]::UTF8.GetBytes($r.Content)
                $hashBytes = $sha.ComputeHash($bytes)
                $resObj.BodyHashSHA256 = -join ($hashBytes | ForEach-Object { "{0:x2}" -f $_ })
            }
        } else {
            # HEAD / Redirect checks
            try {
                $r = Invoke-WebRequest -Uri $u.Url -Method Head -UseBasicParsing -MaximumRedirection 0 -ErrorAction Stop
                $resObj.StatusCode = [int]$r.StatusCode
                $resObj.StatusDescription = $r.StatusDescription
            } catch [System.Net.WebException] {
                $resp = $_.Exception.Response
                if ($resp) {
                     $resObj.StatusCode = [int]$resp.StatusCode
                     $resObj.StatusDescription = $resp.StatusDescription
                     if ($resp.Headers["Location"]) {
                         $resObj.RedirectLocation = $resp.Headers["Location"]
                     }
                } else {
                    $resObj.StatusCode = 500
                    $resObj.StatusDescription = $_.Exception.Message
                }
            }
        }
    } catch {
        $resObj.StatusCode = 500
        $resObj.StatusDescription = $_.Exception.Message
    }

    $results += $resObj
}

# Save JSON
$jsonPath = Join-Path $PSScriptRoot "http_probe_results.json"
$results | ConvertTo-Json -Depth 4 | Set-Content -Path $jsonPath

# Save MD
$mdPath = Join-Path $PSScriptRoot "http_probe_results.md"
$mdContent = "# Reporte Técnico de Pruebas HTTP`n`n**Fecha:** $(Get-Date)`n`n| Nombre | URL | Método | Status | Length | Location/Hash |`n|---|---|---|---|---|---|`n"

foreach ($r in $results) {
    $extra = ""
    if ($r.RedirectLocation) { $extra = "Redir: " + $r.RedirectLocation }
    elseif ($r.BodyHashSHA256) { $extra = "SHA256: " + $r.BodyHashSHA256.Substring(0, 8) + "..." }
    
    $mdContent += "| $($r.Name) | $($r.Url) | $($r.Method) | **$($r.StatusCode)** | $($r.ContentLength) | $extra |`n"
}

$mdContent | Set-Content -Path $mdPath

Write-Host "Pruebas completadas. Resultados en $jsonPath y $mdPath"
