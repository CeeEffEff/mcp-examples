from lance.file import LanceFileReader, LanceFileWriter
import lance

# import pandas as pd
import pyarrow as pa
import pyarrow.dataset
# import pyarrow as pa

# data = pa.table({"x": range(1000)})
# with LanceFileWriter("/tmp/test_file.lance", version="2.1") as writer:
#   writer.write_batch(data)

reader = LanceFileReader(
    "file:///Users/conor.fehilly/.continue/index/lancedb/docs_Ollama__nomic-embed-text__500.lance/data/736c1460-fc1d-4996-aab7-337d8a7b572d.lance"
    # c35161cb-9fcb-4e12-b98c-d2437df57e88.lance"
    # d2ae61c3-f690-4f34-b564-2b1e520db4a4.lance"
)

dataset = lance.dataset(
    "/Users/conor.fehilly/.continue/index/lancedb/docs_Ollama__nomic-embed-text__500.lance"
)
assert isinstance(dataset, pa.dataset.Dataset)
# print(dataset)
df = dataset.to_table().to_pandas()
# df.to_csv("lance_docs.csv")
print(df["starturl"].tail())

print(df.tail())
