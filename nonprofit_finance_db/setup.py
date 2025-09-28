"""
Setup script for nonprofit finance database with bank statement parser
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Nonprofit finance database with bank statement parsing capabilities"

# Read requirements from requirements.txt
def read_requirements():
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="nonprofit-finance-db",
    version="1.0.0",
    author="Software Freelancer AI Expert",
    author_email="your-email@example.com",
    description="Nonprofit finance database with bank statement parsing and duplicate detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/nonprofit-finance-db",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Accounting",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.10.1",
            "flake8>=6.1.0",
            "mypy>=1.6.1",
            "pre-commit>=3.5.0",
        ],
        "web": [
            "flask>=3.0.0",
            "flask-cors>=4.0.0",
            "gunicorn>=21.2.0",
        ],
        "export": [
            "xlsxwriter>=3.1.9",
            "reportlab>=4.0.7",
        ]
    },
    entry_points={
        "console_scripts": [
            "nonprofit-import=scripts.import_statements:main",
            "nonprofit-db-init=scripts.init_db:main",
        ],
    },
    package_data={
        "app": ["*.py"],
        "parsers": ["*.py"],
        "detection": ["*.py"],
        "ingestion": ["*.py"],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="nonprofit finance database bank statement parser duplicate detection",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/nonprofit-finance-db/issues",
        "Source": "https://github.com/yourusername/nonprofit-finance-db",
    },
)