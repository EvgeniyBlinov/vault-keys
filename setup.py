from setuptools import setup, find_packages
from os.path import join, dirname

def parse_requirements(filename):
    """ load requirements from a pip requirements file """
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]

install_reqs = parse_requirements('requirements.txt')

setup(
    name='vault-keys',
    version='0.0.1',
    packages=find_packages(),
    install_requires=install_reqs,
    long_description=open(join(dirname(__file__), 'README.md')).read(),
    entry_points={
        'console_scripts': ['vault-keys=vault_keys.command_line:main'],
    }
)
