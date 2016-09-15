# -*- coding: utf-8 -*-
# Fabfile to:
#    - update the remote system(s)
#    - download and install an

# Import Fabric's API module
from fabric.api import *
import os

env.local_dir = os.path.join(os.path.dirname(__file__), '')
env.user = 'root'
env.hosts = ['fcgomes.com.br', ]

PROJECT_URL = 'git@github.com:fcgomes92/fab-flask-example.git'
UWSGI_FILE = """
[uwsgi]
chdir = {1}
virtualenv = {0}

module = app:app

socket = {0}/bin/app.uwsgi.socket
chmod-socket = 664
vacuum = true

die-on-term = true

master = true
processes = 6
threads = 3

stats = 0.0.0.0:9090
""".strip()

WSGI_INI_FILE = """
description "uWSGI instance to serve {}"

start on runlevel [2345]
stop on runlevel [!2345]

setuid {}
setgid www-data

script
    cd {}
    . bin/activate
    cd {}
    uwsgi --ini wsgi.ini
end script
""".strip()


NGINX_FILE = """
"""


def update_upgrade():
    run("aptitude update")
    run("aptitude -y upgrade")


def create_wsgi_ini():
    local_file = os.path.join(env.local_dir, 'local_wsgi.ini')
    with cd('/etc/init/'):
        with open(local_file, 'w') as f:
            f.write(WSGI_INI_FILE.format(
                'fab-flask-example', 'www-data', env.venv, env.remote_dir))
            f.close()
        put(local_file, 'fab_flask_example.ini')


def create_uwsgi_file():
    local_file = os.path.join(env.local_dir, 'local_uwsgi.ini')
    with cd(env.remote_dir):
        with open(local_file, 'w') as f:
            f.write(UWSGI_FILE.format(env.venv,
                                      env.remote_dir))
            f.close()
        put(local_file, 'wsgi.ini')


def create_nginx_conf():
    pass


def create_venv():
    run('mkdir {} -p'.format(env.venv))
    with cd(env.remote_base):
        run('virtualenv -p python3 {}'.format('fab-flask-example'))


def clone_project():
    with cd(env.venv):
        run('git clone {}'.format(PROJECT_URL))


def update_project():
    with cd(env.remote_dir):
        run('git pull')


def configure():
    env.remote_home_dir = os.path.join('/home', env.user)
    env.remote_base = '/apps'
    env.remote_dir = os.path.join(
        '/apps', 'fab-flask-example', 'fab-flask-example')

    env.venv = os.path.join('/apps', 'fab-flask-example',)
    env.python = os.path.join(env.venv, 'bin', 'python')
    env.pip = os.path.join(env.venv, 'bin', 'pip')

    env.manage_py = os.path.join(env.remote_dir, 'manage.py')
    env.requirements = os.path.join(env.remote_dir, 'requirements.txt')


def deploy():
    # update_upgrade()
    configure()
    create_venv()
    update_project()
    # try:
    #     with cd(env.remote_dir):
    #         run('{} install -r requirements.txt'.format(env.pip))
    # except Exception:
    #     print('não rolou...')
    create_wsgi_ini()
    create_uwsgi_file()
    env.restart_server = lambda: run('sudo service uwsgi restart')
