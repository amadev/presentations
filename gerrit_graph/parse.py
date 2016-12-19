import os
import json
import datetime
from collections import OrderedDict
import sqlite3
import glob


def parse(fn):
    changes = json.load(open(fn))
    for change in changes:
        id = change['change_id']
        detail = json.load(open('raw/%s.json' % id))
        row = OrderedDict()
        row['change_id'] = id
        row['author'] = detail['owner']['username']
        row['verified'] = int(detail['labels']['Verified'].get('value', 0))
        row['code_review'] = int(detail['labels']['Code-Review'].get('value', 0))
        for field in ("project", "branch", "topic",
                      "subject", "status", "mergeable",
                      "insertions", "deletions"):
            row[field] = change.get(field, '')
        for field in ("created", "updated"):
            row[field] = datetime.datetime.strptime(
                change[field].split('.')[0], "%Y-%m-%d %H:%S:%M")
        row['import_id'] = import_id
        stmt = 'insert into change values (%s)' % ','.join(['?'] * len(row))
        c.execute(stmt, row.values())
    conn.commit()

fns = glob.glob('raw/all-*.json')
conn = sqlite3.connect('changes.db')
c = conn.cursor()
dt = datetime.datetime.fromtimestamp(os.path.getmtime('raw'))
c.execute('insert into import (created) values (?)', [dt])
conn.commit()
import_id = c.lastrowid
for fn in fns:
    parse(fn)
conn.close()
