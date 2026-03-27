# ============================================================
# PySpark Job - P11 Fruits Feature Extraction
# Bucket  : oc-p11-fruits
# Input   : s3://oc-p11-fruits-0326-577449504279-eu-west-3-an/data/raw/Training
# Output  : s3://oc-p11-fruits-0326-577449504279-eu-west-3-an/results/
# Submit  : spark-submit --master yarn --deploy-mode cluster \
#               --executor-memory 4g --executor-cores 2 \
#               s3://oc-p11-fruits-0326-577449504279-eu-west-3-an/scripts/pyspark_job.py
# ============================================================

import os
import io
import warnings
import logging
from typing import Iterator

# Suppress TensorFlow logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")
logging.getLogger("py4j").setLevel(logging.ERROR)
logging.getLogger("pyspark").setLevel(logging.ERROR)

import numpy as np
import pandas as pd
from PIL import Image

import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, pandas_udf, element_at, split, udf
from pyspark.sql.types import ArrayType, FloatType
from pyspark.ml.feature import PCA
from pyspark.ml.linalg import Vectors, VectorUDT


# ============================================================
# PATHS
# ============================================================
PATH_DATA   = "s3://oc-p11-fruits-0326-577449504279-eu-west-3-an/data/raw/Training"
PATH_FEATURES = "s3://oc-p11-fruits-0326-577449504279-eu-west-3-an/results/features"
PATH_PCA      = "s3://oc-p11-fruits-0326-577449504279-eu-west-3-an/results/pca"


# ============================================================
# 1. SPARKSESSION
# ============================================================
print("===== Starting SparkSession =====")
spark = (
    SparkSession.builder
    .appName("P11-Fruits-EMR")
    .config("spark.sql.execution.arrow.pyspark.enabled", "true")
    .config("spark.python.worker.timeout", "600")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")
sc = spark.sparkContext

print(f"✅ SparkSession created — Spark {spark.version}")


# ============================================================
# 2. LOAD IMAGES FROM S3
# ============================================================
print(f"\n===== Loading images from {PATH_DATA} =====")
images = (
    spark.read.format("binaryFile")
    .option("pathGlobFilter", "*.jpg")
    .option("recursiveFileLookup", "true")
    .load(PATH_DATA)
)

# Add label column extracted from folder name
images = images.withColumn("label", element_at(split(images["path"], "/"), -2))

count = images.count()
print(f"✅ {count} images loaded")
images.select("path", "label").show(5, truncate=80)


# ============================================================
# 3. MOBILENETV2 + BROADCAST WEIGHTS
# ============================================================
print("\n===== Loading MobileNetV2 and broadcasting weights =====")
base_model = MobileNetV2(
    weights="imagenet",
    include_top=False,
    input_shape=(224, 224, 3),
    pooling="avg"
)
model_weights = base_model.get_weights()
broadcast_weights = sc.broadcast(model_weights)

size_mb = sum(w.nbytes for w in model_weights) / 1024 / 1024
print(f"✅ Weights broadcast — {len(model_weights)} tensors — {size_mb:.1f} MB")


# ============================================================
# 4. PANDAS UDF — FEATURE EXTRACTION (Spark 3.x syntax)
# ============================================================
@pandas_udf(ArrayType(FloatType()))
def featurize_udf(content_series_iter: Iterator[pd.Series]) -> Iterator[pd.Series]:
    """
    Iterator Pandas UDF : le modèle est chargé une seule fois par worker,
    puis appliqué sur chaque batch d'images.
    """
    local_model = MobileNetV2(weights=None, include_top=False, pooling="avg")
    local_model.set_weights(broadcast_weights.value)

    for content_series in content_series_iter:
        def process(content):
            try:
                img = Image.open(io.BytesIO(content)).convert("RGB").resize((224, 224))
                arr = np.expand_dims(img_to_array(img), axis=0)
                return local_model.predict(preprocess_input(arr), verbose=0)[0].tolist()
            except Exception as e:
                print(f"⚠️ Error processing image: {e}")
                return None
        yield content_series.apply(process)


# ============================================================
# 5. FEATURE EXTRACTION + SAVE
# ============================================================
print("\n===== Extracting features =====")
df_features = (
    images.repartition(24)
    .withColumn("features", featurize_udf(col("content")))
)

# Filter failed extractions
df_features = df_features.filter(col("features").isNotNull())
df_features = df_features.select("path", "label", "features")

# Cache before writing
df_features.cache()
extracted_count = df_features.count()
print(f"✅ Features extracted for {extracted_count} images")

# Save features as Parquet
df_features.write.mode("overwrite").parquet(PATH_FEATURES)
print(f"✅ Features saved to {PATH_FEATURES}")


# ============================================================
# 6. PCA
# ============================================================
print("\n===== Running PCA =====")

# Convert array<float> → MLlib Vector
array_to_vector = udf(lambda a: Vectors.dense(a), VectorUDT())
df_pca_input = df_features.withColumn("features_vector", array_to_vector("features"))

# Find optimal k (95% explained variance)
print("   Fitting PCA with k=200 to find optimal k...")
pca_explorer = PCA(k=200, inputCol="features_vector", outputCol="pca_features_tmp")
pca_model_tmp = pca_explorer.fit(df_pca_input)

import numpy as np
evr = np.array(pca_model_tmp.explainedVariance.toArray())
cum_evr = np.cumsum(evr)
k95 = int(np.argmax(cum_evr >= 0.95) + 1)
print(f"   k@95% explained variance = {k95}")

# Fit final PCA with optimal k
print(f"   Fitting final PCA with k={k95}...")
pca_final = PCA(k=k95, inputCol="features_vector", outputCol="pca_features")
pca_model = pca_final.fit(df_pca_input)
df_pca_result = pca_model.transform(df_pca_input)

# Save PCA results
df_final = df_pca_result.select("path", "label", "pca_features")
df_final.write.mode("overwrite").parquet(PATH_PCA)
print(f"✅ PCA results saved to {PATH_PCA}")


# ============================================================
# 7. CLEANUP
# ============================================================
df_features.unpersist()
spark.stop()
print("\n===== Job completed successfully =====")
