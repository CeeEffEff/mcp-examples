import json

# Define the payload as a raw string with triple double quotes
payload = """{
  "serviceName": "google.firestore.v1.Firestore",
  "rpcName": "/google.firestore.v1.Firestore/Commit",
  "request": {
    "payload": "{\n  \"database\": \"projects/prj-croud-dev-seomax/databases/seomax-fs--df0c755fa65b5cbf\",\n  \"writes\": [\n    {\n      \"update\": {\n        \"name\": \"projects/prj-croud-dev-seomax/databases/seomax-fs--df0c755fa65b5cbf/documents/JOBS/L5JS8QRDPQECWYC3A3YZ\",\n        \"fields\": {\n          \"id\": {\n            \"stringValue\": \"L5JS8QRDPQECWYC3A3YZ\"\n          },\n          \"owner_name\": {\n            \"nullValue\": 0\n          },\n          \"start_ts\": {\n            \"nullValue\": 0\n          },\n          \"config\": {\n            \"nullValue\": 0\n          },\n          \"categorisation\": {\n            \"arrayValue\": {\n              \"values\": []\n            }\n          },\n          \"sample\": {\n            \"arrayValue\": {\n              \"values\": []\n            }\n          },\n          \"status_current\": {\n            \"mapValue\": {\n              \"fields\": {\n                \"updated_at\": {\n                  \"timestampValue\": \"2025-08-18T19:55:42.884441Z\"\n                },\n                \"status\": {\n                  \"integerValue\": \"7\"\n                },\n                \"message\": {\n                  \"stringValue\": \"[aasd] JobExpirationTask scheduled expiration 1970-01-01 00:00:00+00:00 triggered while job was [DRAFTING]\"\n                }\n              }\n            }\n          },\n          \"owner_id\": {\n            \"nullValue\": 0\n          },\n          \"job_origin\": {\n            \"stringValue\": \"API\"\n          },\n          \"created_at\": {\n            \"timestampValue\": \"2025-08-18T19:43:08.964883Z\"\n          },\n          \"client_id\": {\n            \"nullValue\": 0\n          },\n          \"expires_at\": {\n            \"nullValue\": 0\n          },\n          \"status_history\": {\n            \"arrayValue\": {\n              \"values\": [\n                {\n                  \"mapValue\": {\n                    \"fields\": {\n                      \"updated_at\": {\n                        \"timestampValue\": \"2025-08-18T19:43:08.964937Z\"\n                      },\n                      \"status\": {\n                        \"integerValue\": \"0\"\n                      },\n                      \"message\": {\n                        \"nullValue\": 0\n                      }\n                    }\n                  }\n                },\n                {\n                  \"mapValue\": {\n                    \"fields\": {\n                      \"updated_at\": {\n                        \"timestampValue\": \"2025-08-18T19:55:42.884441Z\"\n                      },\n                      \"status\": {\n                        \"integerValue\": \"7\"\n                      },\n                      \"message\": {\n                        \"stringValue\": \"[aasd] JobExpirationTask scheduled expiration 1970-01-01 00:00:00+00:00 triggered while job was [DRAFTING]\"\n                      }\n                    }\n                  }\n                }\n              ]\n            }\n          },\n          \"notified\": {\n            \"booleanValue\": false\n          },\n          \"updated_at\": {\n            \"timestampValue\": \"2025-08-18T19:43:08.965497Z\"\n          },\n          \"job_id\": {\n            \"stringValue\": \"L5JS8QRDPQECWYC3A3YZ\"\n          },\n          \"job_name\": {\n            \"nullValue\": 0\n          },\n          \"owner_last_name\": {\n            \"nullValue\": 0\n          },\n          \"client_name\": {\n            \"nullValue\": 0\n          }\n        }\n      },\n      \"updateTransforms\": []\n    }\n  ],\n  \"transaction\": \"\"\n}",
    "requestMethod": "grpc",
    "metadata": {
      "google-cloud-resource-prefix": "projects/prj-croud-dev-seomax/databases/seomax-fs--df0c755fa65b5cbf",
      "x-goog-request-params": "database=projects/prj-croud-dev-seomax/databases/seomax-fs--df0c755fa65b5cbf",
      "x-goog-api-client": "gl-python/3.9.23 grpc/1.73.1 gax/2.25.1"
    }
  },
  "metadata": {
    "google-cloud-resource-prefix": "projects/prj-croud-dev-seomax/databases/seomax-fs--df0c755fa65b5cbf",
    "x-goog-request-params": "database=projects/prj-croud-dev-seomax/databases/seomax-fs--df0c755fa65b5cbf",
    "x-goog-api-client": "gl-python/3.9.23 grpc/1.73.1 gax/2.25.1"
  }
}"""

# Parse the outer JSON
outer_data = json.loads(payload)

# Extract and parse the inner JSON string from "payload"
inner_payload = outer_data["request"]["payload"]
inner_data = json.loads(inner_payload)

# Extract the document update
write = inner_data["writes"][0]["update"]
fields = write["fields"]

# Extract relevant job information
job_id = fields["id"]["stringValue"]
status_current = fields["status_current"]["mapValue"]["fields"]["status"][
    "integerValue"
]
status_message = fields["status_current"]["mapValue"]["fields"]["message"][
    "stringValue"
]
created_at = fields["created_at"]["timestampValue"]
updated_at = fields["updated_at"]["timestampValue"]
status_history = fields["status_history"]["arrayValue"]["values"]

# Format the status history
history = []
for entry in status_history:
    entry_fields = entry["mapValue"]["fields"]
    status = entry_fields["status"]["integerValue"]
    updated_at = entry_fields["updated_at"]["timestampValue"]
    history.append({"status": status, "updated_at": updated_at})
