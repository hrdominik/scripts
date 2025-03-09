
"""
Script for my Raspberry Pi that runs as an cronjob every 1h
gets the current network status

using speedtest-cli from ookla


@author: DHR
@last-modified: 24.01.2022
"""

import logging as log
import subprocess
import json

def speedTest():
    # speedtest -f json
    subP = subprocess.Popen("speedtest -f json", shell=True, stdout=subprocess.PIPE)
    if  subP.stderr:
        raise Exception
    else:
        return subP.stdout.read().decode("utf-8")


def main():
    logFilename = '/var/logs/speedtest/speedtest.log'
    log.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', filename=logFilename, level=log.INFO, datefmt='%Y-%m-%d %H:%M:%S')

    try:
        speedTestJson = json.loads(speedTest())
        networkStatus = "download: {}, upload: {}, ping: {} on {}"
        log.info(networkStatus.format(speedTestJson['download']['bytes'], speedTestJson['upload']['bytes'], speedTestJson['ping']['latency'], speedTestJson['server']['location']))
    except:
        log.warning('No Connection')


if __name__ == "__main__":
    main()
