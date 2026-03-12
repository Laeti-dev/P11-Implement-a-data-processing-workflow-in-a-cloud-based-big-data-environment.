# Implement a Big Data Environment on AWS

OpenClassrooms • [Ai Engineer track](https://openclassrooms.com/fr/paths/795-ai-engineer) • [Laetitia Ikusawa](https://www.linkedin.com/in/laetitia-ikusawa/)
***

## Business Objetives
- **Raise public awareness about fruit biodiversity** by making fruit identification accessible to the general public through a mobile app.
- **Build a scalable fruit classification engine** that will serve as the foundation for intelligent fruit-picking robots, enabling species-specific harvesting treatments.
- **Establish a Big Data architecture on AWS** (EMR, S3, IAM) designed to handle rapidly growing data volumes as the product scales.
- **Develop a PySpark-based image processing pipeline** including feature extraction via a pre-trained TensorFlow model and dimensionality reduction (PCA), ready for distributed computing at scale.
- **Ensure GDPR compliance** by configuring all cloud infrastructure on European servers to protect user data.
- **Optimize infrastructure costs** by maintaining EMR instances only during testing and demos, avoiding unnecessary cloud spending.
- **Position "Fruits!" as an AgriTech innovator** by demonstrating early technical capability in computer vision and distributed data processing, building credibility before scaling.
- **Preserve fruit biodiversity long-term** by enabling precision robotics that can treat each fruit species differently during harvesting.

## Learning Objectives
### Core Technical Skills

- **Master PySpark for distributed data processing**, including writing and optimizing scripts designed to scale with increasing data volumes.
- **Implement a Big Data pipeline end-to-end**, from raw image ingestion to feature extraction and dimensionality reduction, using a distributed computing framework.
- **Integrate a pre-trained TensorFlow/Keras model within a PySpark environment**, specifically learning how to broadcast model weights across cluster nodes to enable efficient distributed inference.
- **Apply dimensionality reduction (PCA) using PySpark's MLlib** to reduce high-dimensional feature vectors extracted from fruit images.

### Cloud & Infrastructure Skills

- **Deploy and configure an AWS EMR cluster**, demonstrating the ability to set up a fully operational Big Data environment in the cloud.
- **Work with AWS services** (EMR, S3, IAM) to build a scalable and cost-efficient architecture.
- **Apply GDPR constraints in a technical context**, specifically by configuring cloud infrastructure to restrict data processing to European territory.

### Professional & Analytical Skills

- **Read and build upon existing code**, by appropriating a former colleague's notebook and extending it with new processing steps.
- **Deliver a critical analysis of the implemented Big Data solution**, evaluating its strengths, limitations, and relevance before broader deployment.
- **Manage infrastructure costs responsibly**, by understanding the financial implications of cloud usage and adopting best practices such as shutting down instances when not in use.
***
## Installation

This project uses **Poetry** to manage Python dependencies and a **Docker container** to provide the runtime environment (Java + Spark + PySpark).
You can edit notebooks locally in your IDE, but all heavy computations (PySpark, Java) run inside the container.

### 1. Prerequisites

- **Docker** installed and running on your machine.
- **Poetry** installed globally on your host (for local development and lockfile management).
- This repository cloned locally:

```bash
git clone <REPO_URL>
cd P11-Implement-a-data-processing-workflow-in-a-cloud-based-big-data-environment
```

You do **not** need to install Java or Spark directly on your host; they are provided by the Docker image.

### 2. Dependency management with Poetry (host side)

Poetry is used to:

- define dependencies in `pyproject.toml`
- lock exact versions in `poetry.lock`

On your host (outside Docker), you can update or inspect dependencies with commands such as:

```bash
poetry lock        # regenerate the lockfile if needed
poetry add <pkg>   # add a new dependency
poetry update      # update dependencies
```

The container build process installs the dependencies listed in `poetry.lock` so that the runtime inside Docker matches the project specification.

### 3. Building the Docker image (runtime with Java + Spark)

From the project root (where the `Dockerfile` and `pyproject.toml` live), build the image:

```bash
docker build -t pyspark-env .
```

This image:

- starts from a slim Python base image,
- installs Java (via the system package manager),
- downloads and configures Apache Spark,
- installs all Python dependencies with Poetry (including PySpark and notebook tooling).

### 4. Starting the container and Jupyter server

Run an interactive container and mount the project directory:

```bash
docker run --rm -it -p 8888:8888 -v "$PWD":/app pyspark-env /bin/bash
```

Inside the container:

```bash
cd /app
poetry run jupyter lab --ip=0.0.0.0 --no-browser --allow-root
```

Jupyter will start and print URLs similar to:

```text
http://e05ee06d2728:8888/lab?token=XXXXXXXXXXXXXXXXXXXXXXXXXXXX
http://127.0.0.1:8888/lab?token=XXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

The **server URL** is typically:

```text
http://127.0.0.1:8888/
```

and the **token** is the value after `token=` in the URL.

### 5. Working from your text editor (Cursor/VS Code) using the container kernel

You can keep editing notebooks locally in your editor and execute them using the Jupyter kernel running inside the container.

1. **Start the container and Jupyter** as described above.
2. **In your editor**, open the notebook you want to run (for example `notebooks/notebook2026.ipynb`).
3. Open the **kernel / interpreter selector** (e.g. “Select Kernel” or similar).
4. Choose **“Existing Jupyter Server”** or **“Connect to Jupyter Server”**.
5. When prompted:
   - **Server URL**: `http://127.0.0.1:8888/` (or `http://localhost:8888/`)
   - **Token**: paste the token printed by Jupyter in the container logs.
6. Confirm the connection. Your editor should now list the kernels exposed by the container.
7. Select the Python kernel associated with this project (created by Poetry inside the container).

From this point on:

- **Editing** happens locally in your IDE (on your host filesystem, mounted as `/app` in the container).
- **Execution** of notebook cells happens **inside the Docker container**, using the configured Java + PySpark environment.

If you restart the container, a new token will be generated. Reconnect your editor using the new server URL/token pair.
