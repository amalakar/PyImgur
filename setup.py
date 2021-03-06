import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

PACKAGE_NAME = 'pyimgur'

HERE = os.path.abspath(os.path.dirname(__file__))
INIT = open(os.path.join(HERE, PACKAGE_NAME, '__init__.py')).read()
README = open(os.path.join(HERE, 'README.md')).read()

VERSION = "0.3.2"

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    author='Andreas Damgaard Pedersen',
    author_email='andreas.damgaard.pedersen@gmail.com',
    url='https://github.com/Damgaard/PyImgur',
    description=('The easy way of using Imgur.'),
    long_description=README,
    classifiers=['Development Status :: 4 - Beta',
                 'Environment :: Console',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: GNU General Public License (GPL)',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python :: 2.7',
                 'Topic :: Utilities'],
    license='GPLv3',
    keywords='imgur api wrapper PyImgur',
    packages=[PACKAGE_NAME],
    package_data={'': ['COPYING'], PACKAGE_NAME: ['*.ini']},
    install_requires=['decorator', 'requests', 'oauth2'],
    test_suite='pyimgur',
    )
