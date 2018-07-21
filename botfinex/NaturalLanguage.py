import config
import requests
import json

# Parses the syntax of the given text using the google natural language API
def parseSyntax(text):
    key = config.googleCloud['API_KEY']
    url = "https://language.googleapis.com/v1beta1/documents:analyzeSyntax?key={}".format(key)
    requestBody = {
        "document": {
            "type": "PLAIN_TEXT",
            "content": text
        }
    }
    r = requests.post(url, json=requestBody)
    response = json.loads(r.text)
    # parse into a readable format (word, tag ie. P, X,V ERB, type ie. ROOT, NOUN)
    syntax = [(x['text']['content'], x['partOfSpeech']['tag'], x['dependencyEdge']['label'])
            for x in response['tokens']]
    return syntax