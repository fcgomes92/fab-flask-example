# -*- coding: utf-8 -*-
# Fabfile to:
#    - update the remote system(s)
#    - download and install an

# Import Fabric's API module
from fabric.api import env, put, cd, run, sudo, local
import os

env.local_dir = os.path.join(os.path.dirname(__file__), '')
env.user = 'root'
env.hosts = ['fcgomes.com.br', ]
env.configured = False

PROJECT_URL = 'git@github.com:fcgomes92/fab_flask_example.git'
APP_NAME = 'fab_flask_example'
SYSTEM_DEPS = []
RUN_USER = 'www-data'
RUN_GROUP = 'www-data'
STATIC_URL = '/static/'
STATIC_DIR = '/apps/fab_flask_example/fab_flask_example/example_app/static/'
INIT_DIR = '/etc/init'
SITES_AVAILABLE = '/etc/nginx/sites-available'
SITES_ENABLED = '/etc/nginx/sites-enabled'
SERVER_NAMES = ['fcgomes.com.br', 'www.fcgomes.com.br', ]


def _is_dir(d): return lambda x: bool(
    int(run('if test -d {}; then echo 1; else echo 0; fi'.format(d))))


def _exists(f): return lambda x: bool(
    int(run('if test -f {}; then echo 1; else echo 0; fi'.format(f))))


def nginx(op): return lambda x: sudo('service nginx {}'.format(op))


def wsgi(init, op): return lambda x: sudo('service {} {}'.format(init, op))


def _generate_uwsgi_ini(app_dir, venv_dir, sock_path):
    """
    :param app_dir:
    :param venv_dir:
    :param sock_path:
    :return str:
    """
    return """
        [uwsgi]
        chdir = {0}
        virtualenv = {1}

        module = app:app

        socket = {2}
        chmod-socket = 664
        vacuum = true

        die-on-term = true

        master = true
        processes = 6
        threads = 3

        stats = 0.0.0.0:9090
        """.strip().format(app_dir, venv_dir, sock_path)


def _generate_wsgi_ini(app_name, run_user, run_group,
                       venv_dir, app_dir):
    """
    :param app_name:
    :param run_user:
    :param run_group:
    :param venv_dir:
    :param app_dir:
    :return str:
    """
    return """
        description "uWSGI instance to serve {0}"

        start on runlevel [2345]
        stop on runlevel [!2345]

        setuid {1}
        setgid {2}

        script
            cd {3}
            . bin/activate
            cd {4}
            uwsgi --ini wsgi.ini
        end script
        """.strip().format(
        app_name, run_user, run_group, venv_dir, app_dir)


def _generate_nginx_conf(server_name, log_path, static_url,
                         static_dir, app_name, sock_path):
    """
    :param server_name:
    :param log_path:
    :param static_url:
    :param static_dir:
    :param app_name:
    :param sock_path:
    :return str:
    """
    return """
        server {{
            listen 80;
            server_name {0};

            client_max_body_size 4G;

            access_log {1}/nginx-access-gpi-api.log;
            error_log {1}/nginx-error-gpi-api.log;

            location = /favicon.ico {{
                access_log off; log_not_found off;
            }}

            location {2} {{
                autoindex on;
                alias {3};
            }}

            location / {{
                include uwsgi_params;
                uwsgi_pass  unix:{4};
            }}
        }}""".strip().format(server_name, log_path, static_url, static_dir,
                             sock_path)


def _create_wsgi_ini():
    local_file = os.path.join(env.local_dir, 'local_wsgi.ini')
    if not _is_dir(env.init_dir):
        raise ValueError("Init dir ({}) doesn't exist!".format(env.init_dir))

    with cd(env.init_dir):
        with open(local_file, 'w') as f:
            f.write(
                _generate_wsgi_ini(env.app_name, env.run_user, env.run_group,
                                   env.venv, env.app_dir))
            f.close()
        put(local_file, env.init)
        os.remove(local_file)


def _create_uwsgi_file():
    local_file = os.path.join(env.local_dir, 'local_uwsgi.ini')
    if not _is_dir(env.app_dir):
        raise ValueError("App dir ({}) doesn't exist!".format(env.app_dir))

    with cd(env.app_dir):
        with open(local_file, 'w') as f:
            f.write(_generate_uwsgi_ini(
                env.app_dir, env.venv, env.sock_path))
            f.close()
        put(local_file, 'wsgi.ini')
        os.remove(local_file)


def _create_nginx_conf():
    if not env.configured:
        configure()
    local_file = os.path.join(env.local_dir, 'nginx.conf')
    conf_name = '{}.conf'.format(env.app_name)
    if not _is_dir(env.sites_available) or not _is_dir(env.sites_enabled):
        raise ValueError("Sites Availabe doesn't exist!")

    with cd(env.sites_available):
        with open(local_file, 'w') as f:
            f.write(_generate_nginx_conf(
                ' '.join(sn for sn in env.server_names), env.log_path,
                env.static_url, env.static_dir, env.app_name, env.sock_path))
            f.close()
        put(local_file, conf_name)
        if _exists(os.path.join(env.sites_enabled, conf_name)):
            sudo('rm {}'.format(os.path.join(env.sites_enabled, conf_name)))
        sudo('ln -s {} {}'.format(os.path.join(env.sites_available, conf_name),
                                  env.sites_enabled))
        os.remove(local_file)


def _create_venv():
    if not env.configured:
        configure()
    if not _is_dir(env.venv):
        run('mkdir {} -p'.format(env.venv))
    with cd(os.path.dirname(env.venv)):
        run('virtualenv -p python3 {}'.format(env.app_name))


def _clone_project():
    if _is_dir(env.app_dir):
        update_app()
    else:
        with cd(env.venv):
            run('git clone {}'.format(PROJECT_URL))


def _create_log_folder():
    if not env.configured:
        configure()
    if not _is_dir(env.log_path):
        run('mkdir {} -p'.format(env.log_path))


def _build_static():
    if not env.configured:
        configure()
    with cd(env.app_dir):
        run('chmod +x build-static.sh')
        run('./build-static.sh')


def sys_update_upgrade():
    run("aptitude update")
    run("aptitude -y upgrade")


def sys_install_dependencies():
    if len(SYSTEM_DEPS) > 0:
        run("aptitude install -y {}"
            .format(' '.join(dep for dep in SYSTEM_DEPS)))


def update_app():
    if not env.configured:
        configure()
    if _is_dir(env.app_dir):
        with cd(env.app_dir):
            run('git pull')


def configure():
    env.configured = True

    env.app_name = APP_NAME
    env.app_dir = '/apps/{0}/{0}'.format(APP_NAME)
    env.venv = '/apps/{0}'.format(APP_NAME)

    env.sock_path = os.path.join(env.venv, 'bin', '{}.sock'.format(APP_NAME))

    env.python = os.path.join(env.venv, 'bin', 'python')
    env.pip = os.path.join(env.venv, 'bin', 'pip')

    env.static_url = STATIC_URL
    env.static_dir = STATIC_DIR

    env.log_path = os.path.join(env.venv, 'log')
    env.init_dir = INIT_DIR
    env.init = '{}.conf'.format(APP_NAME)

    env.sites_available = SITES_AVAILABLE
    env.sites_enabled = SITES_ENABLED
    env.server_names = SERVER_NAMES

    env.run_user = RUN_USER
    env.run_group = RUN_GROUP
    # for Django projects
    # env.manage_py = os.path.join(env.app_dir, 'manage.py')
    env.requirements = os.path.join(env.app_dir, 'requirements.txt')


def commit(msg=None):
    if not msg:
        msg = """A great commit message explaining: All These Things That I've Done!"""
    local("""
    cd {0}; git add . ; git commit -am "{1}" ; git push origin master;
    """.format(env.local_dir, msg))


def full_deploy(update=False, clone=False, commit_msg=None):
    commit(commit_msg)
    if int(update):
        sys_update_upgrade()
    _create_venv()
    _create_log_folder()
    if int(clone):
        _clone_project()
    else:
        update_app()
    _build_static
    _create_wsgi_ini()
    _create_uwsgi_file()
    _create_nginx_conf()
    nginx('reload')


def deploy():
    update_upgrade()
    _create_venv()
    update_app()
    _create_wsgi_ini()
    _create_uwsgi_file()
