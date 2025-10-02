@echo off
echo ================================================
echo 10回連続シミュレーション実行 - 協力行動調査
echo ================================================

for /L %%i in (1,1,10) do (
    echo.
    echo ================ RUN %%i/10 ================
    echo Run %%i starting at %time%
    python main.py > output_run_%%i.txt 2>&1
    echo Run %%i completed at %time%
)

echo.
echo ================================================
echo 全10回のテスト完了！結果ファイル:
echo output_run_1.txt ～ output_run_10.txt
echo ================================================

echo.
echo 群れ狩りの発生回数を集計中...
findstr /c:"GROUP HUNT" output_run_*.txt > group_hunt_summary.txt
findstr /c:"🤝" output_run_*.txt >> group_hunt_summary.txt
findstr /c:"🎯.*GROUP HUNT FORMED" output_run_*.txt >> group_hunt_summary.txt
findstr /c:"🎉.*GROUP HUNT SUCCESS" output_run_*.txt >> group_hunt_summary.txt

echo 集計結果は group_hunt_summary.txt に保存されました
pause