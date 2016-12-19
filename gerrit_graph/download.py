import os
import requests
import json
import shutil
import datetime
import logging


host = 'https://review.openstack.org/'
change_url = 'changes/%s/detail/'
life_time_weeks = 6
dt_format = '%Y-%m-%d %H:%S:%M'


def calc_periods():
    curr = datetime.datetime.now()
    curr = curr.replace(hour=23, minute=59, second=59, microsecond=0)
    periods = []
    for i in range(life_time_weeks + 1):
        end = curr
        start = curr - datetime.timedelta(days=6)
        start = start.replace(hour=0, minute=0, second=0)
        periods.append([start, end])
        curr -= datetime.timedelta(days=7)
    return periods


def remove_first_line(text):
    return '\n'.join(text.split('\n')[1:])


def load_changes(start, end):
    conditions = [
        'status:open',
        'project:openstack/nova']
    if start:
        conditions.append('after:"%s"' % start.strftime(dt_format))
    conditions.append('before:"%s"' % end.strftime(dt_format))
    logging.debug('Getting changes with conditions %s', conditions)
    r = sess.get(
        host + 'changes/',
        params={'q': ' '.join(conditions)})
    data = remove_first_line(r.text)
    if not data:
        return
    fn = 'raw/all-%s-%s.json' % (
        None if not start else start.strftime('%Y-%m-%d'),
        end.strftime('%Y-%m-%d'))
    f = open(fn, 'w')
    f.write(data.encode('utf8'))
    f.close()

    jdata = json.load(open(fn))

    for change in jdata:
        r = sess.get(host + change_url % change['id'])
        data = remove_first_line(r.text)
        f = open('raw/%s.json' % change['change_id'], 'w')
        f.write(data.encode('utf8'))
        f.close()


if __name__ == '__main__':
    if os.path.exists('raw'):
        shutil.rmtree('raw')
    os.mkdir('raw')
    sess = requests.Session()
    periods = calc_periods()
    periods[-1][0] = None
    for period in periods:
        load_changes(*period)
