function buildbook () {
    git pull
    cd "./Bible"
    message=$(bash "buildbook.sh")
    cd ..
    git add .
    git commit -m "$message"
    git push
}
trap "kill $botpid" EXIT
#
while true; do
    buildbook
    python3.11 "bot.py" &
    botpid=$!
    sleep 24h
    kill botpid
done