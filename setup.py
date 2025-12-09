from setuptools import setup, find_packages

setup(
    name="photobot",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "folium",
        "exifread",
        "Pillow",
        "streamlit>=1.25",
        "streamlit-folium>=0.11",
        "shapely"
    ],
    entry_points={
        "console_scripts": [
            "photobot=photobot.cli:main"
        ]
    },
    author="Arthur Cabon",
    description="Outil CLI pour trier et cartographier des photos par date et lieu",
    python_requires=">=3.8"
)
