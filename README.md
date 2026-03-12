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

This project uses **Poetry** for Python dependencies and **Docker** for the runtime (Java + Spark + PySpark). You can edit notebooks in your IDE; execution runs inside the container.

Follow the steps below in order. You do **not** need to install Java or Spark on your host.

---

### Step 1 — Prerequisites

- **Docker** installed and running ([Get Docker](https://docs.docker.com/get-docker/)).
- **Poetry** installed on your machine ([Install Poetry](https://python-poetry.org/docs/#installation)) — used for dependency management and lockfile.
- This repository cloned:

```bash
git clone <REPO_URL>
cd P11-Implement-a-data-processing-workflow-in-a-cloud-based-big-data-environment
```

---

### Step 2 — Set up Kaggle (required for the dataset download cell)

The notebook downloads the [Fruits dataset](https://www.kaggle.com/datasets/moltean/fruits) from Kaggle. To make that work from inside the container, you need to provide your Kaggle API credentials via a `.env` file.

1. **Create a Kaggle account** (if you don't have one): [kaggle.com](https://www.kaggle.com/).

2. **Get your API key**:
   - Log in to Kaggle → click your profile picture (top right) → **Settings**.
   - In **API**, click **Create New Token**. This downloads a `kaggle.json` file containing `username` and `key`.

3. **Create a `.env` file** in the **project root** (same folder as `Dockerfile` and `README.md`). Do **not** commit this file (it is listed in `.gitignore`).

   Create `.env` with exactly these two lines (replace with your own values):

   ```bash
   KAGGLE_USERNAME=your_kaggle_username
   KAGGLE_TOKEN=your_kaggle_api_key
   ```

   - `KAGGLE_USERNAME`: the `username` value from `kaggle.json`.
   - `KAGGLE_TOKEN`: the `key` value from `kaggle.json`.

4. **Why this works**: When you start the container with `--env-file .env` (Step 4), these variables are available inside the container. The notebook cell then writes a `kaggle.json` from them and runs `kaggle datasets download` to fetch the fruits dataset into `/app/data/fruits`. No need to copy `kaggle.json` into the repo or into the image.

---

### Step 3 — Build the Docker image

From the project root:

```bash
docker build -t pyspark-env .
```

The image includes Python, Java, Apache Spark, and the project's Poetry dependencies (PySpark, Jupyter, etc.).

---

### Step 4 — Start the container and Jupyter

Run the container and mount the project. **Use `--env-file .env`** so Kaggle credentials are available (see Step 2):

```bash
docker run --rm -it \
  -p 8888:8888 \
  --env-file .env \
  -e KAGGLE_CONFIG_DIR=/app/.kaggle \
  -v "$PWD":/app \
  -w /app \
  pyspark-env /bin/bash
```

- `--env-file .env` — loads `KAGGLE_USERNAME` and `KAGGLE_TOKEN` (and any other vars in `.env`) into the container.
- `-e KAGGLE_CONFIG_DIR=/app/.kaggle` — tells the Kaggle CLI where to write `kaggle.json` inside the container.
- `-v "$PWD":/app` — mounts the current project directory as `/app` in the container.
- `-w /app` — working directory inside the container is `/app`.

Inside the container, start Jupyter:

```bash
cd /app
poetry run jupyter lab --ip=0.0.0.0 --no-browser --allow-root
```

Jupyter will print URLs like:

```text
http://127.0.0.1:8888/lab?token=XXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

- **Server URL**: `http://127.0.0.1:8888/` (or `http://localhost:8888/`)
- **Token**: the string after `token=` in the URL.

---

### Step 5 — Run the notebook (including the Kaggle download cell)

1. Open `notebooks/notebook2026.ipynb` in your browser (Jupyter Lab) or in your editor (see Step 6).
2. Run the cells in order. The **Configuration** section defines `PROJECT_ROOT` and paths; run it before the Kaggle cell.
3. The cell that loads `.env`, sets `KAGGLE_USERNAME` / `KAGGLE_TOKEN`, creates `kaggle.json`, and runs `!kaggle datasets download -d moltean/fruits -p /app/data/fruits --unzip` will work as long as you created `.env` (Step 2) and started the container with `--env-file .env` (Step 4).

If you see an error about missing `KAGGLE_USERNAME` or `KAGGLE_TOKEN`, check that `.env` exists in the project root and that you launched the container with `--env-file .env`.

---

### Step 6 — (Optional) Use the container kernel from your editor

You can edit notebooks in Cursor/VS Code and run them against the Jupyter server inside the container.

1. Start the container and Jupyter as in Step 4.
2. In your editor, open the notebook (e.g. `notebooks/notebook2026.ipynb`).
3. Open the **kernel / interpreter selector** (e.g. “Select Kernel”).
4. Choose **“Existing Jupyter Server”** or **“Connect to Jupyter Server”**.
5. Enter:
   - **Server URL**: `http://127.0.0.1:8888/` (or `http://localhost:8888/`)
   - **Token**: the token printed by Jupyter in the container.
6. Select the Python kernel from the container.

Editing is done locally; execution runs inside the container. If you restart the container, reconnect with the new token.

---

### Dependency management (Poetry, host side)

Dependencies are defined in `pyproject.toml` and locked in `poetry.lock`. The Docker build installs from the lockfile. On your host you can run:

```bash
poetry lock        # regenerate the lockfile if needed
poetry add <pkg>   # add a new dependency
poetry update      # update dependencies
```

Rebuild the Docker image after changing dependencies so the container stays in sync.
