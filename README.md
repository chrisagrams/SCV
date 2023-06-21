# SCV - Sequence Coverage Visualizer
[![Tests](https://github.com/chrisagrams/SCV_V1.1/actions/workflows/api_test.yaml/badge.svg)](https://github.com/chrisagrams/SCV_V1.1/actions/workflows/api_test.yaml)

A web application for protein sequence coverage 3D visualization.

## Publication

- "Sequence Coverage Visualizer: A Web Application for Protein Sequence Coverage 3D Visualization" by Xinhao Shao, Christopher Grams, and Yu Gao.
   Published in Journal of Proteomics, 2023.
   [Link to publication](https://doi.org/10.1021/acs.jproteome.2c00358)

## Table of Contents

- [Description](#description)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)


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

3. Run the Docker container, forwarding port 80 to 8080 (or any other port you wish to use):

   ```bash
   docker run -d -p 8080:80 scv
   ```