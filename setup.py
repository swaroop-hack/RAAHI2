from setuptools import setup, find_packages

setup(
    name="raahi",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi",
        "uvicorn[standard]",
        "sqlalchemy",
        "pydantic",
        "requests",
        "scikit-learn",
        "numpy",
        "pandas",
        "joblib",
        "shapely",
        "networkx",
        "python-dotenv",
    ],
)
