while true; do
	python3.11 bot.py &
	LASTPID=$!

	while true; do
		read -rsn1 quit
		[[ "$quit" == "q" ]] && break
		[[ "$quit" == "b" ]] && break
		[[ $(date +%H:%M:%S) == "23:59:58" ]] && break
		sleep 1
	done
	kill $LASTPID
	[[ "$quit" == "q" ]] && break
	git pull
	cd Bible
	bash buildbook.sh
	cd ..
	git add .
	git commit -m "regenerated full.md"
	git push
done
