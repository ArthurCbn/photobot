from setuptools import setup

setup(
    name="photobot",
    version="1.0.0",
    py_modules=["cli", "map", "sort"],
    package_dir={"": "src"},
    install_requires=[
        "folium",
        "exifread",
        "Pillow"
    ],
    entry_points={
        "console_scripts": [
            "photobot=cli:main"
        ]
    },
    author="Arthur Cabon",
    description="Outil CLI pour trier et cartographier des photos par date et lieu",
    python_requires=">=3.8"
)
