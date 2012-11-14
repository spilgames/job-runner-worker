from setuptools import setup

import job_runner_worker


setup(
    name='job-runner-worker',
    version=job_runner_worker.__version__,
    url='https://github.com/spilgames/dwh/',
    author='Orne Brocaar',
    author_email='orne.brocaar@spilgames.com',
    description='Job-Runner Worker',
    long_description=open('README.rst').read(),
    packages=[
        'job_runner_worker',
    ],
    scripts=[
        'scripts/job_runner_worker',
    ],
    install_requires=[
        'argparse',
        'gevent',
        'gevent_subprocess',
        'requests',
        'pyzmq',
    ]
)
