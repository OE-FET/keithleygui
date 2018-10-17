from setuptools import setup, find_packages

setup(
    name='keithleygui',
    version='0.0.1',
    description="",
    author='Sam Schott',
    author_email='ss2151@cam.ac.uk',
    url='https://github.com/oe-fet/keithleygui.git',
    license='MIT',
    long_description=open('README.md').read(),
    packages=find_packages(),
    package_data={
        'keithleygui': ['*.ui', '*.mplstyle'],
    },
    entry_points={
        'console_scripts': [
            'keithleygui=keithleygui.main:run'
        ],
        'gui_scripts': [
            'keithleygui=keithleygui.main:run'
        ]
    },
    install_requires=[
        'setuptools',
        'QtPy',
        'keithley2600',
        'matplotlib',
        'repr',
    ],
    zip_safe=False,
    keywords='Ktransfer2600',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=[
    ]
)
