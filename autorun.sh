function buildbook () {
    git pull
    cd "./Bible"
    message=$(bash "buildbook.sh")
    cd ..
    git add .
    git commit -m "$message"
    git push
}

buildbook