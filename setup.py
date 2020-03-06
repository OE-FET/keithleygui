from setuptools import setup, find_packages

setup(
    name='keithleygui',
    version='1.1.6',
    description="",
    author='Sam Schott',
    author_email='ss2151@cam.ac.uk',
    url='https://github.com/oe-fet/keithleygui.git',
    license='MIT',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    package_data={
        'keithleygui': ['*.ui', '*/*.ui'],
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
        'keithley2600>=1.2.1',
        'numpy',
        'pyvisa',
        'pyqtgraph>=0.11.0rc0',
        'PyQt5',
        'repr',
        'setuptools',
    ],
    zip_safe=False,
    keywords='keithleygui',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
