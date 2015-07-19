#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

""" Json server to present Avahi found machines. """

import logging
import socket
import sys
import threading

from time import sleep

from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf

from flask import Flask
from flask import jsonify
from flask import render_template
app = Flask(__name__)

targets = {}
global keep_running_flag
keep_running_flag = True

def server_finder():
    zeroconf = Zeroconf()
    browser = ServiceBrowser(zeroconf, "_workstation._tcp.local.", handlers=[on_service_state_change])
    while keep_running_flag:
        sleep(.5)
    zeroconf.close()

def on_service_state_change(zeroconf, service_type, name, state_change):
    global targets
    if state_change is ServiceStateChange.Added:
        info = zeroconf.get_service_info(service_type, name)
        if info:
            targets[info.server[:-1]] = socket.inet_ntoa(info.address)
    else: #  ServiceStateChange.Removed
        del targets[name]

def do_zeroconf_thread():
    global targets
    if len(sys.argv) > 1:
        assert sys.argv[1:] == ['--debug']
        logging.getLogger('zeroconf').setLevel(logging.DEBUG)

    server_finder_thread = threading.Thread(target=server_finder)
    server_finder_thread.start()

    print("Waiting for servers before starting json service...")
    sleep(2.5) # Give the server a second to find devices.
    print("Starting up. Known servers: %s" % (targets.keys()))

def do_json_server():
    @app.route('/servers')
    def known_servers():
        return render_template('targets.html', targets=targets)

    @app.route('/json/servers')
    def json_known_servers():
        return jsonify(targets)

    #@app.route('/user/<username>')
    #def show_user_profile(username):
    #        # show the user profile for that user
    #            return 'User %s' % username
    #@app.route('/post/<int:post_id>')
    #def show_post(post_id):
    #        # show the post with the given id, the id is an integer
    #            return 'Post %d' % post_id

    @app.route('/hello/')
    @app.route('/hello/<name>')
    def hello(name=None):
            return render_template('hello.html', name=name)

    app.run(host='0.0.0.0', debug=True, use_reloader=False)

def main():
    do_zeroconf_thread()
    do_json_server()

if __name__ == '__main__':
    try:
        main()
    finally:
        keep_running_flag = False
