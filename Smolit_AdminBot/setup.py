from setuptools import setup, find_packages

setup(
    name="root_bot",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "psutil>=5.9.0",
        "requests>=2.25.0",
        "python-daemon>=2.3.0",
    ],
    entry_points={
        "console_scripts": [
            "rootbot-daemon=root_bot.__main__:main",
        ],
    },
    scripts=['bin/rootbot'],
    data_files=[
        ('/etc/systemd/system', ['rootbot.service']),
        ('/etc/rootbot', ['docs/examples/rootbot.conf']),
    ],
    author="RootBot Team",
    description="An autonomous system administration bot",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: No Input/Output Interaction",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.8",
        "Topic :: System :: Systems Administration",
    ],
)

