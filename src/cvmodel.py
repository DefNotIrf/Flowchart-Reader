from inference_sdk import InferenceHTTPClient
import json

# Set up Roboflow inference client
CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="your-key-here or set at .env"
)

# Run inference on your image
result = CLIENT.infer(
    "data/images/v1/flowchart_page_3.png",
    model_id="aiboardscannerdatasetcomplete-vvbe4/11"
)

# Save results to JSON for manual adjustment
with open("data/jsonf/flowchart_page_3_roboflow.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

print("Inference complete.")
