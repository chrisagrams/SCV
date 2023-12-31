# SCV - Sequence Coverage Visualizer
[![Tests](https://github.com/chrisagrams/SCV_V1.1/actions/workflows/api_test.yaml/badge.svg)](https://github.com/chrisagrams/SCV_V1.1/actions/workflows/api_test.yaml)

A web application for protein sequence coverage 3D visualization.

## Publication

- "Sequence Coverage Visualizer: A Web Application for Protein Sequence Coverage 3D Visualization" by Xinhao Shao, Christopher Grams, and Yu Gao.
   Published in Journal of Proteomics, 2023.
   [Link to publication](https://doi.org/10.1021/acs.jproteome.2c00358)

## Table of Contents

- [Description](#description)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Dependencies
Make sure you have the following dependencies installed before running the project:

- [Docker](https://www.docker.com/) - Containerization platform used to build and run the application.

If you wish to run the project locally without Docker or Nginx, you will also need to install the following dependencies:
- [Python >= 3.8](https://www.python.org/) - Programming language used to build the backend API.
- [pip](https://pip.pypa.io/en/stable/) - Package installer for Python.
- [PyMOL](https://pymol.org/2/) - Molecular visualization system used to generate the 3D protein structure images.
  - Debian/Ubuntu: `sudo apt-get install pymol`
  - Arch/Manjaro: `sudo pacman -S pymol`
  - macOS: `brew install pymol`
  - Windows: *See [Open-Source PyMOL - PyMOL Wiki](https://pymolwiki.org/index.php/Windows_Install#Open-Source_PyMOL)*

## Installation
To run this project locally using Docker, follow the steps below:

1. Clone the repository:

   ```bash
   git clone https://github.com/chrisagrams/SCV_V1.1.git
   cd SCV_V1.1
   ```

2. Build the Docker image from the Dockerfile:
   
   ```bash
   docker build -t scv .
   ```

3. Run the Docker container, forwarding port 80 to 8080 (or any other port you wish to use) and attaching the db folder to the container:

   ```bash
   docker run -v ./db:/db -d -p 8080:80 scv
   ```
   
## Configuration
The application uses the following files for configuration: ".env", "rates.json", and "logging.ini".