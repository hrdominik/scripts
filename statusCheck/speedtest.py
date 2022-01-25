
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
    logFilename = 'speedtest.log'
    format = '%(asctime)s:%(levelname)s; %(message)s'
    log.basicConfig(filename=logFilename, level=log.INFO, format=format)

    try:
        speedTestJson = json.loads(speedTest())
        networkStatus = "download: {}, upload: {}, ping: {} on {}"
        log.info(networkStatus.format(speedTestJson['download']['bytes'], speedTestJson['upload']['bytes'], speedTestJson['ping']['latency'], speedTestJson['server']['location']))
    except:
        log.warning('No Connection')


if __name__ == "__main__":
    main()