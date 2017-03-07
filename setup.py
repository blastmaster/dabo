from setuptools import setup

setup(
        name='dabo',
        version='0.0.1',
        description='dabo - a minimalistic flask-based dashboard application.',
        long_description='',
        license='MIT License',
        packages=['dabo'],
        py_modules=['run'],
        install_requires=[
            'flask',
            'praw',
            'requests',
            'newspaper3k'
        ],
)
