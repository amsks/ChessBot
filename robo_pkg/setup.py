 
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="robo_pkg", # Replace with your own username
    version="0.0.1",
    author="Benjamin Berta",
    author_email="berta@capus.tu-berlin.de",
    description="Package for Robotics & AI course",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.tubit.tu-berlin.de/benjaminberta/robotics_lab.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
