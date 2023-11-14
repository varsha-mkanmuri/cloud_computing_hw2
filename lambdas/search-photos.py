import json
import boto3
import urllib.parse
import inflection

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from botocore.exceptions import ClientError

REGION = 'us-east-1'
HOST = 'search-photos-bt6qgfib7ts4wqyqdvy52wod5u.aos.us-east-1.on.aws'
INDEX = 'photos'

# Define the client to interact with Lex
client = boto3.client('lexv2-runtime')


def lambda_handler(event, context):
    print("Event codepipeline 2")
    print(event)
    # print(event["queryStringParameters"])
    input = event['q']
    # input = event['messages'][0]['unstructured']['text']
    #input = "show me zero and octopi"
    # Initiate conversation with Lex
    response = client.recognize_text(
        botId='ANOYBOEGUT',  # MODIFY HERE
        botAliasId='OH0S4RECIE',  # MODIFY HERE
        localeId='en_US',
        sessionId='testuser',
        text=input)

    keywords = []
    
    
    print('event', event)

    interpretations = response['interpretations']
    for interpretation in interpretations:
        if 'nluConfidence' in interpretation.keys():
            intent = interpretation['intent']
            intent_name = intent['name']

            if intent_name == 'SearchIntent':
                slots = intent['slots']
                print(slots, 'slots')
                for slot_name,slot_value in slots.items():
                    if slot_value is not None:
                        keyword = slots[slot_name]['value']['interpretedValue']
                        keywords.append(keyword)

    print(keywords)
    
    if len(keywords) < 1:
        return {
        'statusCode': 200,
        'body': json.dumps({"search_result": []})
        }

    key_words_singularized = []

    for keyword in keywords:
        singularized_label = inflection.singularize(keyword.lower())
        key_words_singularized.append(singularized_label.lower())

    print(key_words_singularized)
    search_results_urls = query(key_words_singularized)

    search_results = list(set(search_results_urls))

    # done
    return {
        'statusCode': 200,
        'body': json.dumps({"search_result": search_results})
    }


def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)


def query(keywords):
    should_condition = [{'multi_match': {'query': keyword}} for keyword in keywords]

    q = {
        'size': 5,
        'query': {
            'bool': {
                'should': should_condition
            }
        }
    }

    client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
        http_auth=get_awsauth(REGION, 'es'),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection)
    res = client.search(index=INDEX, body=q)
    print(res)
    hits = res['hits']['hits']
    results = []

    search_results_urls = []

    for hit in hits:
        objectKey = hit['_source']['objectKey']
        bucket = hit['_source']['bucket']
        s3_image_url = "https://s3.amazonaws.com/" + bucket + "/" + objectKey
        search_results_urls.append(s3_image_url)

    print(search_results_urls)
    return search_results_urls
