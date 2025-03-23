from setuptools import setup, find_packages

setup(
    name="docscoop",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "python-magic>=0.4.27",
        "google-generativeai>=0.3.1",
        "python-dotenv>=1.0.0",
        "tqdm>=4.66.1",
        "PySocks>=1.7.1",
        "stem>=1.8.1",
    ],
    entry_points={
        'console_scripts': [
            'docscoop=docscoop_cli:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for scanning the web for publicly accessible sensitive documents",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/docscoop",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
    ],
    python_requires=">=3.7",
) 