$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ids = @('89927','89891','89937','89859','89939','89938','89918','89879','89876','89909','89899','89896','89886','89913','89893')
$dirs = Get-ChildItem -LiteralPath 'Ex1\subs-2026B' -Directory
$out = @()
foreach ($id in $ids) {
    $d = $dirs | Where-Object { $_.Name -match "_${id}_" } | Select-Object -First 1
    if ($d) {
        $f = Join-Path $d.FullName 'os1.c'
        $out += "========== $($d.Name) =========="
        if (Test-Path -LiteralPath $f) {
            $out += (Get-Content -LiteralPath $f -Raw -Encoding UTF8)
        } else {
            $out += "(no os1.c)"
        }
    } else {
        $out += "========== id $id =========="
        $out += "(no matching dir)"
    }
}
$out -join "`n" | Out-File -FilePath part_b_dump.txt -Encoding UTF8
(Get-Item part_b_dump.txt).Length
