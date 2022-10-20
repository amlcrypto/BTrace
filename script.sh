#1/bin/bash

source /opt/scripts/Btrace/venv/bin/activate
cd /opt/scripts/BTrace
pip install -r requirements.txt
alembic upgrade head

cp btracer.service /etc//systemd//system/btracer.service
systemctl daemon-reload
systemctl enable btracer.service
systemctl start btracer.service