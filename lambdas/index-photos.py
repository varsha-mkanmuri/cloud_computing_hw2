import json
import urllib.parse
import boto3
import inflection
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from botocore.exceptions import ClientError

REGION = 'us-east-1'
HOST = 'search-photos-bt6qgfib7ts4wqyqdvy52wod5u.us-east-1.es.amazonaws.com'
INDEX = 'photos'


def lambda_handler(event, context):
    rekognition_client = boto3.client('rekognition')
    s3_client = boto3.client('s3')

    try:
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            objectKey = record['s3']['object']['key']
            createdTimestamp = record['eventTime']

            print('objectKey', objectKey)

            s3_meta_data_response = s3_client.head_object(Bucket=bucket, Key=objectKey)
            print('-------------------------\n')
            print('s3_meta_data_response', s3_meta_data_response)
            s3_headers = s3_meta_data_response['ResponseMetadata']['HTTPHeaders']
            custom_labels = ''
            if 'x-amz-meta-customlabels' in s3_headers:
                custom_labels = s3_headers['x-amz-meta-customlabels']
                custom_labels_list = custom_labels.split(",")
            print('custom_labels', custom_labels)
            print('\n-------------------------')

            s3_image_url = "https://s3.amazonaws.com/" + bucket + "/" + objectKey
            print("bucket", bucket)
            print("objectKey", objectKey)
            print("createdTimestamp", createdTimestamp)
            print("s3_image_url", s3_image_url)

            labels_response = rekognition_client.detect_labels(
                Image={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': objectKey,
                    }
                },
                MinConfidence=0.7,
                MaxLabels=10
            )

            # printing
            labels = labels_response['Labels']
            print('labels_response', labels_response)
            print('labels', labels)
            output_labels = []
            for label in labels:
                singularized_label = inflection.singularize(label['Name'].lower())
                output_labels.append(singularized_label.lower())
            print(output_labels)
            if custom_labels:
                for label in custom_labels_list:
                    singularized_label = inflection.singularize(label.lower())
                    output_labels.append(singularized_label.lower())
            print(output_labels)

            output_labels = list(set(output_labels))

            opensearch_record = {'objectKey': objectKey,
                                 'bucket': bucket,
                                 'createdTimestamp': createdTimestamp,
                                 'labels': output_labels}
            print('opensearch_record', opensearch_record)

            insert(opensearch_record)
            # print('query_params', output_labels[0] + ',' + output_labels[1])
            query()


    except Exception as e:
        print(e)
        print('Error indexing image')


def insert(record):
    try:
        client = OpenSearch(hosts=[{
            'host': HOST,
            'port': 443
        }],
            http_auth=get_awsauth(REGION, 'es'),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection)

        response = client.index(
            index=INDEX,
            body=record,
            refresh=True
        )

        print('\nAdding document:')
        print(response)

    except ClientError as e:
        print('Error', e.response['Error']['Message'])


def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)


# local testing and cleanup
def query_delete(term):
    q = {'size': 5, 'query': {'multi_match': {'query': term}}}
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

    for hit in hits:
        client.delete(
            index=INDEX,
            id=hit['_id']
        )
    print(results)


# local testing
def query():
    q = {'size': 5, 'query': {'match_all': {}}}
    print("query formed", q)
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

    print(hits)
