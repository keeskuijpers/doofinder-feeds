#!/bin/zsh
export PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/local/bin
set -a; source /Users/keeskuijpers/retailz-server/.env; set +a
cd /Users/keeskuijpers/doofinder-feeds || exit 1
python3 generate_feed.py >> sync.log 2>&1 || { echo "$(date) generate FAILED" >> sync.log; exit 1; }
git add -A
if ! git diff --cached --quiet; then
  git commit -q -m "feed update $(date +%F\ %H:%M)"
  git push -q origin HEAD && echo "$(date) pushed" >> sync.log
else
  echo "$(date) no changes" >> sync.log
fi
