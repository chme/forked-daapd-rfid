#!/usr/bin/env python

from setuptools import setup

setup(name='musicbox-daapd',
    version='0.0.1',
    description='Musicbox based on forked-daapd.',
    install_requires=['RPi.GPIO', 'MFRC522-python', 'aiohttp'],
    packages=['server'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: POSIX :: Linux",
    ],
    entry_points={
        'console_scripts': [
            'musicbox-daapd=server.main:main'
        ],
    },
    data_files=[
        ('/etc', ['musicbox-daapd.conf']),
        ('/usr/share/musicbox-daapd/htdocs',
            [
                'htdocs/index.html'
            ]
        ),  # noqa
        ('/usr/share/musicbox-daapd/htdocs/static/css',
            [
                'htdocs/static/css/app.css',
                'htdocs/static/css/chunk-vendors.css'
            ]
        ),  # noqa
        ('/usr/share/musicbox-daapd/htdocs/static/js',
            [
                'htdocs/static/js/app.js',
                'htdocs/static/js/app.js.map',
                'htdocs/static/js/chunk-vendors.js',
                'htdocs/static/js/chunk-vendors.js.map'
            ]
        ),  # noqa
        ('/usr/share/musicbox-daapd/htdocs/static/img',
            [
                'htdocs/static/img/materialdesignicons-webfont.svg'
            ]
        ),  # noqa
        ('/usr/share/musicbox-daapd/htdocs/static/fonts',
            [
                'htdocs/static/fonts/materialdesignicons-webfont.eot',
                'htdocs/static/fonts/materialdesignicons-webfont.ttf',
                'htdocs/static/fonts/materialdesignicons-webfont.woff',
                'htdocs/static/fonts/materialdesignicons-webfont.woff2'
            ]
        ),  # noqa
    ])
