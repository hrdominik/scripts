
"""
Script for my Raspberry Pi that runs as an cronjob every 1h
gets the current network status

using speedtest-cli from ookla


@author: DHR
@last-modified: 11.03.2026
"""

import logging as log
import subprocess
import json
import os
from datetime import datetime, timedelta

def speedTest():
    # speedtest -f json
    subP = subprocess.Popen("speedtest --accept-gdpr -f json", shell=True, stdout=subprocess.PIPE)
    if  subP.stderr:
        raise Exception
    else:
        return subP.stdout.read().decode("utf-8")

def preFlightCheck():
    try:
        subprocess.check_output("ping -c 1 -W 5 google.com", shell=True)
        return True
    except subprocess.CalledProcessError:
        return False


LOGFILE = '/stacks/logs/speedtest/speedtest.log'
SPEEDTEST_INTERVAL = timedelta(hours=1)


def lastSpeedTestTime():
    if not os.path.exists(LOGFILE):
        return None
    try:
        with open(LOGFILE, 'r') as f:
            lines = f.readlines()
        for line in reversed(lines):
            if 'download:' in line:
                return datetime.strptime(line[:19], '%Y-%m-%d %H:%M:%S')
    except Exception:
        pass
    return None


def main():
    log.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', filename=LOGFILE, level=log.INFO, datefmt='%Y-%m-%d %H:%M:%S')

    try:
        if not preFlightCheck():
             raise Exception
        last = lastSpeedTestTime()
        if (last is None or datetime.now() - last >= SPEEDTEST_INTERVAL):
            speedTestJson = json.loads(speedTest())
            networkStatus = "download: {}, upload: {}, ping: {} on {}"
            log.info(networkStatus.format(speedTestJson['download']['bytes'], speedTestJson['upload']['bytes'], speedTestJson['ping']['latency'], speedTestJson['server']['location']))
    except:
        log.warning('No Connection')


if __name__ == "__main__":
    main()
