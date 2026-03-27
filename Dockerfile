FROM python:3.11-slim-bookworm

# Install Java
RUN apt-get update && apt-get install -y openjdk-17-jdk curl unzip && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the Java home directory
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
# Add Java to the PATH
ENV PATH="$JAVA_HOME/bin:$PATH"

# Install Spark (simplified example, version to adjust)
ENV SPARK_VERSION=3.5.3
# Set the Hadoop version
ENV HADOOP_VERSION=3
# Download and extract Spark
RUN curl -L "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" \
  | tar -xz -C /opt
# Set the Spark home directory
ENV SPARK_HOME=/opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}
# Add Spark to the PATH
ENV PATH="$SPARK_HOME/bin:$PATH"

# Install AWS CLI v2
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip" && \
  unzip awscliv2.zip && \
  ./aws/install && \
  rm -rf awscliv2.zip aws

# Install Python deps
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install

# Default command: notebook
CMD ["poetry", "run", "jupyter", "lab", "--ip=0.0.0.0", "--no-browser", "--allow-root"]
