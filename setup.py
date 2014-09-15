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
        'cfg': [
            'role = cfg:make_role',
            'network = cfg:make_network',
            'hostname = cfg:make_hostname',
            'openstack = cfg:make_openstack',
        ],
    }
)
