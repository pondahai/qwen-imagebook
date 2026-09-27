import json
import urllib.request
import sys

COMFY_URL = "http://100.89.149.50:8188"

def load_template():
    with open(r"api\template.json") as f:
        return json.load(f)

def gen_page(num, prompt, seed=1234, steps=30, width=1024, height=1024):
    t = load_template()
    t["prompt"]["4"]["inputs"]["prompt"] = prompt
    t["prompt"]["4"]["inputs"]["resolution"] = width
    t["prompt"]["5"]["inputs"]["width"] = width
    t["prompt"]["5"]["inputs"]["height"] = height
    t["prompt"]["6"]["inputs"]["seed"] = seed
    t["prompt"]["6"]["inputs"]["steps"] = steps
    t["prompt"]["8"]["inputs"]["filename_prefix"] = f"page{num}"
    
    data = json.dumps(t).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    print(f"Page {num}: prompt_id={result['prompt_id']}")
    return result["prompt_id"]

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python api_script.py <page_num> <prompt>")
    else:
        num = int(sys.argv[1])
        prompt = sys.argv[2]
        gen_page(num, prompt)
