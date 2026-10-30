import subprocess
import requests

url = "https://timeapi.io/api/time/current/zone?timeZone=America/New_York"
sudo_password = "q1r4w2e3t5!A"

response = requests.get(url, timeout=10)
response.raise_for_status()

data = response.json()
new_time = data["dateTime"].split(".")[0]

print("Internet time:", new_time)

subprocess.run(
    ["sudo", "-S", "date", "-s", new_time],
    input=sudo_password + "\n",
    text=True,
    check=True,
    stdout=subprocess.PIPE
)

print("Pi time:", subprocess.check_output(["date"], text=True).strip())
