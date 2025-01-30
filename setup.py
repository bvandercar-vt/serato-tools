from setuptools import find_packages, setup

setup(
    name="serato_tags",
    version="1.1",
    description="Serato track metadata tags",
    author="TODO",
    author_email="TODO",
    packages=["serato_tags", "serato_tags.utils"],
    package_dir={"serato_tags": "scripts"},
    install_requires=["mutagen"],
    extras_require={"waveform_drawing": ["PIL"]},
)
