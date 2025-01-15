import requests

SLACK_BOT_TOKEN = "xoxb-8274787141655-8302057324481-m6rSI96bmytk4jVHb4bJZC9z"
EMAIL = "mamemimomu0820@gmail.com"
url = "https://slack.com/api/users.lookupByEmail"
headers = {
    "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
}
params = {"email": EMAIL}

response = requests.get(url, headers=headers, params=params)
print(response.json())