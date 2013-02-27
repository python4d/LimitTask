cd C:\Users\damien\eclipse_workspace\LimitTask
pygmentize -f html -O encoding='utf-8',style=colorful,linenos=inline -o LimitTask_with_lines.html -l python LimitTask.pyw
pygmentize -f html -O encoding='utf-8',style=colorful -o LimitTask_without_lines.html -l python LimitTask.pyw
pause > nul