from setuptools import setup, find_packages

setup(
    name='es-setup',
    version='0.0.1',
    packages=find_packages(),
    author='Dunrong Huang',
    author_email='riegamaths@gmail.com',
    description='a command line for build RDO',
    license='GPLv3',
    keywords='RDO OpenStack',
    entry_points={
        'console_scripts': [
            'es-setup = es_setup.main:main',
        ],

        'es_setup.cfg': [
            'role = es_setup.cfg:make_role',
            'network = es_setup.cfg:make_network',
            'hostname = es_setup.cfg:make_hostname',
            'openstack = es_setup.cfg:make_openstack',
        ],
    },
)
