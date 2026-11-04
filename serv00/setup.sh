#!/bin/sh
# Run on Serv00 over SSH:  sh setup.sh https://YOURAPP.onrender.com PORT
UPSTREAM="$1"; PORT="$2"; D="$HOME/xiaozhi-relay"; mkdir -p "$D"; cd "$D"
cp "$(dirname "$0")/relay.py" . 2>/dev/null
python3 -m venv venv && . venv/bin/activate
AIOHTTP_NO_EXTENSIONS=1 MULTIDICT_NO_EXTENSIONS=1 YARL_NO_EXTENSIONS=1 FROZENLIST_NO_EXTENSIONS=1 PROPCACHE_NO_EXTENSIONS=1 pip install aiohttp
cat > run.sh <<RUN
#!/bin/sh
cd $D && . venv/bin/activate && UPSTREAM=$UPSTREAM PORT=$PORT exec python relay.py
RUN
chmod +x run.sh
# supervisor: start now, and re-check every 10 min
( crontab -l 2>/dev/null | grep -v xiaozhi-relay; echo "*/10 * * * * pgrep -f 'python relay.py' >/dev/null || nohup $D/run.sh >> $D/relay.log 2>&1 &  # xiaozhi-relay" ) | crontab -
nohup ./run.sh >> relay.log 2>&1 &
sleep 3; tail -3 relay.log; echo "relay started on port $PORT"
