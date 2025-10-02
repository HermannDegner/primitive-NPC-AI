Write-Host "================================================"
Write-Host "10回連続シミュレーション実行 - 協力行動調査"
Write-Host "================================================"

Set-Location "d:\GitHub\primitive-NPC-AI"

for ($i = 1; $i -le 10; $i++) {
    Write-Host ""
    Write-Host "================ RUN $i/10 ================"
    Write-Host "Run $i starting at $(Get-Date -Format 'HH:mm:ss')"
    
    python main.py > "output_run_$i.txt" 2>&1
    
    Write-Host "Run $i completed at $(Get-Date -Format 'HH:mm:ss')"
}

Write-Host ""
Write-Host "================================================"
Write-Host "全10回のテスト完了！結果ファイル:"
Write-Host "output_run_1.txt ～ output_run_10.txt"
Write-Host "================================================"

Write-Host ""
Write-Host "群れ狩りの発生回数を集計中..."

# 群れ狩りのパターンを検索
Select-String -Pattern "GROUP HUNT" -Path "output_run_*.txt" | Out-File "group_hunt_summary.txt"
Select-String -Pattern "🤝" -Path "output_run_*.txt" | Add-Content "group_hunt_summary.txt"
Select-String -Pattern "GROUP HUNT FORMED" -Path "output_run_*.txt" | Add-Content "group_hunt_summary.txt"
Select-String -Pattern "GROUP HUNT SUCCESS" -Path "output_run_*.txt" | Add-Content "group_hunt_summary.txt"

Write-Host "集計結果は group_hunt_summary.txt に保存されました"
Read-Host "Enterキーを押してください"