import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="autolabel",
    version="0.0.1",
    author="wheelos",
    author_email="daohu527@gmail.com",
    description="Auto label tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wheelos/autolabel",
    project_urls={
        "Bug Tracker": "https://github.com/wheelos/autolabel/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    install_requires=[
        "opencv-python",
        "requests"
    ],
    entry_points={
        'console_scripts': [
            'autolabel = autolabel.cmd:main',
        ],
    },
    python_requires=">=3.6",
)
