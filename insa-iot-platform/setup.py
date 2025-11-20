#!/usr/bin/env python3
"""
Alkhorayef ESP IoT Platform - Setup Configuration
"""

from setuptools import setup, find_packages
import os

# Read long description from README
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

# Read requirements
def read_requirements(filename):
    with open(filename, encoding='utf-8') as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith('#')
        ]

setup(
    name='alkhorayef-esp-iot-platform',
    version='1.0.0',
    description='Intelligent ESP pump diagnostics with AI-powered knowledge graph RAG system',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    author='Alkhorayef Petroleum Company',
    author_email='support@alkhorayef.com',
    url='https://github.com/alkhorayef/esp-iot-platform',
    license='Proprietary',

    # Package configuration
    packages=find_packages(exclude=['tests', 'tests.*', 'docs', 'scripts']),
    include_package_data=True,
    zip_safe=False,

    # Python version requirement
    python_requires='>=3.11',

    # Dependencies
    install_requires=read_requirements('requirements.txt'),

    # Optional dependencies
    extras_require={
        'dev': [
            'pytest>=7.4.4',
            'pytest-asyncio>=0.23.3',
            'pytest-cov>=4.1.0',
            'pytest-mock>=3.12.0',
            'black>=24.1.1',
            'flake8>=7.0.0',
            'mypy>=1.8.0',
            'isort>=5.13.2',
            'pylint>=3.0.3',
        ],
        'docs': [
            'mkdocs>=1.5.3',
            'mkdocs-material>=9.5.3',
        ],
        'monitoring': [
            'prometheus-client>=0.19.0',
            'opentelemetry-api>=1.22.0',
            'opentelemetry-sdk>=1.22.0',
            'opentelemetry-instrumentation-fastapi>=0.43b0',
        ],
    },

    # Entry points
    entry_points={
        'console_scripts': [
            'alkhorayef-esp=app:main',
        ],
    },

    # Package metadata
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: System :: Monitoring',
        'Framework :: FastAPI',
    ],

    keywords=[
        'iot',
        'esp',
        'artificial-lift',
        'oil-gas',
        'petroleum',
        'ai',
        'machine-learning',
        'rag',
        'knowledge-graph',
        'timeseries',
        'diagnostics',
        'predictive-maintenance',
    ],

    project_urls={
        'Documentation': 'https://docs.alkhorayef.com/esp-iot-platform',
        'Source': 'https://github.com/alkhorayef/esp-iot-platform',
        'Tracker': 'https://github.com/alkhorayef/esp-iot-platform/issues',
    },
)
