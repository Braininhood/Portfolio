from setuptools import setup, find_packages

setup(
    name="sentiment_analysis",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask>=2.0.1",
        "transformers>=4.20.1",
        "torch>=2.6.0",
        "numpy>=1.21.0",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A sentiment analysis web application",
    keywords="nlp, sentiment, flask",
    url="https://github.com/yourusername/sentiment_analysis",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Programming Language :: Python :: 3",
    ],
) 