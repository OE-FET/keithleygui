from setuptools import setup, find_packages

setup(
    name="keithleygui",
    version="1.1.8",
    description="A GUI for the Keithley 2600 series",
    author="Sam Schott",
    author_email="ss2151@cam.ac.uk",
    url="https://github.com/oe-fet/keithleygui.git",
    license="MIT",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    package_data={
        "keithleygui": ["*.ui", "*/*.ui"],
    },
    entry_points={
        "console_scripts": ["keithleygui=keithleygui.main:run"],
    },
    python_requires=">=3.6",
    install_requires=[
        "keithley2600>=1.2.1",
        "numpy",
        "pyvisa",
        "pyqtgraph>=0.11.0",
        "PyQt5",
        "repr",
        "setuptools",
    ],
    zip_safe=False,
    keywords="keithleygui",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
