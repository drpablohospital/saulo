#!/bin/bash
cd /home/xiu/.openclaw/workspace/saulo-unified
pkill -f "python.*main.py" 2>/dev/null
sleep 3
source venv/bin/activate
python main.py > /tmp/saulo.log 2>&1 &
sleep 2
echo "Saulo reiniciado"
