import os
import errno
import datetime
import subprocess
import re
import time

import setup_me

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def main():
    mkdir('ngrok')
    data = setup_me.read_settings()
    ip_address = setup_me.get_ip()
    paths = (__location__,'ngrok', 'ngrok.log')
    logfile = os.path.join(*paths)
    if os.path.isfile(logfile):
        os.rename(
            logfile,
            logfile[:-4] + datetime.datetime.now().strftime('%d-%m-%y_%H:%M'))
    subprocess.call(('/home/ru/ngrok/ngrok http {ip}:{port} -log=stdout -log-level=debug' +
                     ' > {logfile} &').format(ip=ip_address,
                                              port=data['port'],
                                              logfile=logfile),
                    shell=True)
    time.sleep(1.2)
    with open(logfile, 'r') as lf:
        data = lf.read().replace('\n', '')
    try:
        ngrok_host = re.search(r'Hostname:\w+.\w+.\w+', data).group(0)[9:]
        with open('ngrok.host', 'w') as nh:
            nh.write(ngrok_host)
    except:
        pass


if __name__ == '__main__':
    main()
