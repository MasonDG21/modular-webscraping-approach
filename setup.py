from setuptools import setup, find_packages

setup(
    name="web-scraper",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "beautifulsoup4>=4.9.3",
        "requests>=2.25.1",
        "selenium>=3.141.0",
        "aiohttp>=3.7.4",
        "python-dotenv>=0.17.1",
        "PyQt5>=5.15.4",
        "chardet>=4.0.0",
    ],
    entry_points={
        "console_scripts": [
            "web-scraper=main:main",
        ],
    },
)