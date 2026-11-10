cd /home/claude/w126/scripts
while true; do
  python3 cells.py > /dev/null 2>&1
  python3 backcast.py > /tmp/bc_inc.log 2>&1
  python3 -c "
import sys,os; sys.path.insert(0,'.'); from common import *
cs=cities(); todo=[c for c in cs.city if os.path.exists(f'{DATA}/cells2/{slug(c)}.parquet') and not os.path.exists(f'{RES}/city/{slug(c)}.json')]
open('/tmp/todo.txt','w').write('\n'.join(todo)); print(len(todo))" > /tmp/todo_n.txt
  python3 city_dml.py @/tmp/todo.txt >> /tmp/city_inc.log 2>&1
  n=$(ls /home/claude/w126/results/city/*.json 2>/dev/null | wc -l)
  [ "$n" -ge 126 ] && break
  sleep 60
done
