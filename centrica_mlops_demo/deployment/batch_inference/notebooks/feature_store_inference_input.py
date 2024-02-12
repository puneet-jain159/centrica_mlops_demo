# Databricks notebook source
import os

notebook_path =  '/Workspace/' + os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
%cd $notebook_path

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

import sys
import os
notebook_path =  '/Workspace/' + os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
%cd $notebook_path
%cd ..
sys.path.append("../..")

# COMMAND ----------

# Name of the current environment
dbutils.widgets.dropdown("env", "dev", ["dev", "staging", "prod"], "Environment Name")
# Delta table to store the predictions table.
dbutils.widgets.text("output_table_name", "mlops_pj.dev_centrica_mlops_demo.feature_store_inference_input", label="Output Table Name")
dbutils.widgets.text(
    "training_data_path",
    "/databricks-datasets/nyctaxi-with-zipcodes/subsampled",
    label="Path to the training data",
)


# COMMAND ----------

env = dbutils.widgets.get("env")
output_table_name = dbutils.widgets.get("output_table_name")
training_data_path = dbutils.widgets.get("training_data_path")
assert output_table_name != "", "output_table_name notebook parameter must be specified"
assert training_data_path != "", "model_name notebook parameter must be specified"

# COMMAND ----------

from pyspark.sql.functions import to_timestamp, lit
from pyspark.sql.types import IntegerType
import math
from datetime import timedelta, timezone

def rounded_unix_timestamp(dt, num_minutes=15):
    """
    Ceilings datetime dt to interval num_minutes, then returns the unix timestamp.
    """
    nsecs = dt.minute * 60 + dt.second + dt.microsecond * 1e-6
    delta = math.ceil(nsecs / (60 * num_minutes)) * (60 * num_minutes) - nsecs
    return int((dt + timedelta(seconds=delta)).replace(tzinfo=timezone.utc).timestamp())


rounded_unix_timestamp_udf = udf(rounded_unix_timestamp, IntegerType())

df = spark.read.format("delta").load(training_data_path)
df.withColumn(
    "rounded_pickup_datetime",
    to_timestamp(rounded_unix_timestamp_udf(df["tpep_pickup_datetime"], lit(15))),
).withColumn(
    "rounded_dropoff_datetime",
    to_timestamp(rounded_unix_timestamp_udf(df["tpep_dropoff_datetime"], lit(30))),
).drop(
    "tpep_pickup_datetime"
).drop(
    "tpep_dropoff_datetime"

).write.mode(
    "overwrite"
).option("mergeSchema", "true"
).saveAsTable(
    name=output_table_name
)

# COMMAND ----------

display(df)

# COMMAND ----------


