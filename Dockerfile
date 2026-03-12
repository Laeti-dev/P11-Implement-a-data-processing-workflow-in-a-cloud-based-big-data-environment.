FROM python:3.11-slim

# Install Java
RUN apt-get update && apt-get install -y default-jdk curl && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="$JAVA_HOME/bin:$PATH"

# Install Spark (simplified example, version to adjust)
ENV SPARK_VERSION=3.5.3
ENV HADOOP_VERSION=3
RUN curl -L "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" \
  | tar -xz -C /opt
ENV SPARK_HOME=/opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}
ENV PATH="$SPARK_HOME/bin:$PATH"

# Install Python deps
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install

# Default command: notebook
CMD ["poetry", "run", "jupyter", "lab", "--ip=0.0.0.0", "--no-browser", "--allow-root"]
