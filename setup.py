from setuptools import setup, find_packages

setup(
    name='keithleygui',
    version='1.0.2',
    description="",
    author='Sam Schott',
    author_email='ss2151@cam.ac.uk',
    url='https://github.com/oe-fet/keithleygui.git',
    license='MIT',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    package_data={
        'keithleygui': ['*.ui', '*.mplstyle'],
    },
    entry_points={
        'console_scripts': [
            'keithleygui=keithleygui.main:run'
        ],
        'gui_scripts': [
            'keithleygui_gui=keithleygui.main:run'
        ]
    },
    install_requires=[
        'setuptools',
        'QtPy',
        'keithley2600',
        'matplotlib',
        'numpy',
        'pyvisa',
        'repr',
    ],
    zip_safe=False,
    keywords='keithleygui',
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
