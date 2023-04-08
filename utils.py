import requests

requests.adapters.DEFAULT_RETRIES = 4

f_API_key = "API_KEY.txt"

with open(f_API_key) as FIN:
    API_KEY = FIN.read().strip()


def query(text, temperature=0.7, max_tokens=200, n=1):

    query_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-type": "application/json",
    }
    base_params = {
        "model": "gpt-3.5-turbo",
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [],
        "n": n,
    }

    params = base_params.copy()
    params["messages"].append({"role": "user", "content": text})

    r = requests.post(query_url, headers=headers, json=params)

    if not r.ok:
        print(r.status_code, r.content)
        exit()

    result = r.json()

    return result
