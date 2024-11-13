from setuptools import setup, find_packages

setup(
    name="root_bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "psutil>=5.9.0",
    ],
    entry_points={
        "console_scripts": [
            "rootbot=root_bot.__main__:main",
        ],
    },
    author="RootBot Team",
    description="An autonomous system administration bot",
    python_requires=">=3.8",
)
