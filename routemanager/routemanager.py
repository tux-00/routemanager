from pyroute2 import IPDB
from flask import Flask, render_template, redirect, url_for, flash, request, g, Markup, jsonify
import sqlite3
import psutil
import os
import time
import math
import click
import sys
import socket

app = Flask(__name__)

app.config.update(
    DATABASE=os.path.join(app.root_path, 'database/clients.db'),
    IF_VPN='tun0',
    SECRET_KEY='101-946-361'
)


#
# Database functions
#
def connect_ipdb():
    ipdb = IPDB()
    return ipdb


def get_ipdb():
    if not hasattr(g, 'ipdb'):
        g.ipdb = connect_ipdb()
    return g.ipdb


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    db = get_db()
    with app.open_resource('database/schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def get_clients_data():
    db = get_db()
    cursor = db.execute('SELECT * FROM clients')
    return cursor.fetchall()


def get_client_data(client_id):
    db = get_db()
    cursor = db.execute('SELECT * FROM clients WHERE id = ?', (client_id,))
    return cursor.fetchone()


def get_tiles_data():
    result = {}
    db = get_db()

    cursor = db.execute('SELECT count(*) FROM clients WHERE status = 1')
    result['active_clients'] = cursor.fetchone()[0]
    cursor = db.execute('SELECT count(*) FROM clients')
    result['total_clients'] = cursor.fetchone()[0]
    result['percent_ram'] = psutil.virtual_memory().percent
    result['days_uptime'] = round((time.time() - psutil.boot_time()) / 86400, 2)
    try:
        result['network_rx'] = convert_size(psutil.net_io_counters(pernic=True)[app.config['IF_VPN']].bytes_recv)
        result['network_tx'] = convert_size(psutil.net_io_counters(pernic=True)[app.config['IF_VPN']].bytes_sent)
    except KeyError:
        result['error'] = 'No interface found: {}'.format(app.config['IF_VPN'])

    return result


def get_client_from_subnet(subnet, subnet_len):
    db = get_db()
    cursor = db.execute('SELECT * FROM clients WHERE lan_subnet = ? and lan_subnet_len = ? and status = 1', (subnet, subnet_len,))
    return cursor.fetchone()


def set_client_status(client_id, client_new_status):
    db = get_db()
    cursor = db.execute('UPDATE clients SET status = ? WHERE id = ?', (client_new_status, client_id,))
    db.commit()
    return True

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.commit()
        g.sqlite_db.close()
    if hasattr(g, 'ipdb'):
        g.ipdb.release()


def add_client(display_name, static_vpn_ip, client_subnet):
    if vpn_ip_exists(static_vpn_ip):
        return False

    if display_name_exists(display_name):
        return False

    if static_vpn_ip == get_ifvpn_ip():
        return False

    db = get_db()

    hostname = convert_display_name(display_name)
    
    # Validate vpn IP
    try:
        socket.inet_aton(static_vpn_ip)
    except socket.error:
        return 'Invalid IP VPN: {}'.format(lan_subnet)
    
    # Validate subnet mask
    try:
        lan_subnet, lan_subnet_len = str.split(client_subnet, '/')
    except ValueError:
        return 'Invalid subnet: {}'.format(client_subnet)

    # Validate lan subnet
    try:
        socket.inet_aton(lan_subnet)
    except socket.error:
        return 'Invalid IP in subnet client: {}'.format(lan_subnet)

    # TODO: try
    db.execute('INSERT INTO clients (hostname, display_name, static_vpn_ip, lan_subnet, lan_subnet_len, status, date_added) values (?, ?, ?, ?, ?, ?, ?)',
               (hostname, display_name, static_vpn_ip, lan_subnet, lan_subnet_len, 0, time.strftime("%y/%m/%d"),))

    return True


def refresh_db():
    db = get_db()
    # TODO: get current routes

    return True


#
# Network functions
#
def get_ifvpn_routes():
    ipdb = get_ipdb()
    oif_id = get_ifvpn_index()
    routes = [x for x in ipdb.routes if x['oif'] == oif_id]
    return routes


def route_exists(lan_subnet):
    routes = get_ifvpn_routes()

    for r in routes:
        if r['dst'].split('/')[0] == lan_subnet:
            print (r['dst'].split('/')[0])
            print (lan_subnet)
            return True
    return False


def get_ifvpn_index():
    ipdb = get_ipdb()
    return ipdb.interfaces[app.config['IF_VPN']].get('index')


def get_ifvpn_ip():
    ipdb = get_ipdb()
    if_vpn = ipdb.interfaces[app.config['IF_VPN']]
    ip = if_vpn.get('ipaddr')
    return ip[0]['address']


def add_ifvpn_route(subnet, subnet_len):
    ipdb = get_ipdb()
    dst = subnet + "/" + str(subnet_len)
    print(dst, get_ifvpn_index())
    ipdb.routes.add(dst=dst, oif=get_ifvpn_index()).commit()
    ipdb.release()

    return True


def del_route(subnet, subnet_len):
    ipdb = get_ipdb()
    dst = subnet + "/" + str(subnet_len)
    try:
        ipdb.routes.remove(ipdb.routes[dst])
    except KeyError as e:
        return False
    ipdb.commit()
    ipdb.release()

    return True


#
# Tools functions
#
def display_name_exists(display_name):
    db = get_db()
    cursor = db.execute('SELECT count(*) FROM clients WHERE display_name = ?', (display_name,))
    if cursor.fetchone()[0] == 0:
        return False
    else:
        return True


def vpn_ip_exists(ip):
    db = get_db()
    cursor = db.execute('SELECT count(*) FROM clients WHERE static_vpn_ip = ?', (ip,))
    if cursor.fetchone()[0] == 0:
        return False
    else:
        return True


def convert_display_name(s):
    return ''.join(filter(str.isalnum, s[0:35])).lower()


def convert_size(size_bytes):
    if (size_bytes == 0):
        return '0B'
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 1)
    return '%s%s' % (s, size_name[i])


#
# Flask App routes
#
@app.route('/', methods=['GET', 'POST'])
def main():
    # Add client
    if request.method == 'POST' and request.form.get('add_client') != '':
        r = add_client(request.form['display_name'], request.form['static_vpn_ip'], request.form['client_subnet'])
        if r == False:
            flash(Markup('Client name or IP VPN submitted already exists.'), 'error')
        elif type(r) == str:
            flash(Markup(r), 'error')
        else:
            flash(Markup('The client <b>%s</b> has been added.' % request.form['display_name']), 'success')

    # Get tiles informations
    tiles = get_tiles_data()
    if 'error' in tiles:
        flash(Markup(tiles['error']), 'error')

    return render_template('index.html', clients=get_clients_data(), tiles=tiles)


@app.route('/change_client_status', methods=['POST'])
def change_client_status():
    # Get form result
    cid = int(request.form['cid'])
    cnewstatus = int(request.form['cnewstatus'])

    # Get client informations
    client = get_client_data(cid)
    client_route_exists = route_exists(client['lan_subnet'])

    # Client enabled
    if cnewstatus == 1:
        if client_route_exists:
            # TODO: display client name with the same route
            duplicate_client = get_client_from_subnet(client['lan_subnet'], client['lan_subnet_len'])
            print('pass')
            print(duplicate_client['display_name'])
            return jsonify(status='exist', cid=0, cstatus=0, duplicate_client=duplicate_client['display_name'])
        else:
            add_ifvpn_route(client['lan_subnet'], client['lan_subnet_len'])
            set_client_status(cid, cnewstatus)

    # Client disabled
    if cnewstatus == 0 and not client_route_exists:
        del_route(client['lan_subnet'], client['lan_subnet_len'])
        set_client_status(cid, cnewstatus)

    # status: exist, error, success
    return jsonify(status='ok', cid=0, cstatus=0)


#
# Flask App CLI
#
@app.cli.command('initdb')
def initdb_command():
    if click.confirm(text='Are you sure you want to drop the database ? Routes will not be removed!', default=False, abort=True):
        init_db()
        print('Database cleared.')
        print('Warning: Routes hasn\'t been removed!')
