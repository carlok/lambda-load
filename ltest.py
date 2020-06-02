import json
import logging
import os
import requests
from requests.exceptions import HTTPError
import urllib3
from string import Template


def data_chunker(data, size):
    return [data[i:i + size] for i in range(0, len(data), size)]


def event_validation_graphql(event):
    if 'country' not in event['body']:
        v_error = 'Validation failed: missing event[body][country]'
        raise Exception(v_error)

    return


def event_validation_reporter(event):
    if 'domainName' not in event['requestContext']:
        v_error = 'Validation failed: missing event[requestContext][domainName]'
        raise Exception(v_error)

    if 'path' not in event['requestContext']:
        v_error = 'Validation failed: missing event[requestContext][path]'
        raise Exception(v_error)

    if 'action' not in event['body']:
        v_error = 'Validation failed: missing event[body][action]'
        raise Exception(v_error)

    if 'bunch' not in event['body']:
        v_error = 'Validation failed: missing event[body][bunch]'
        raise Exception(v_error)

    if 'size' not in event['body']['bunch']:
        v_error = 'Validation failed: missing event[body][bunch][size]'
        raise Exception(v_error)

    if 'data' not in event['body']['bunch']:
        v_error = 'Validation failed: missing event[body][bunch][data]'
        raise Exception(v_error)

    if event['body']['bunch']['size'] != len(event['body']['bunch']['data']):
        v_error = 'Validation failed: mismatching event[body][bunch][size] and len(event[body][bunch][data])'
        raise Exception(v_error)
    return


def graphql(event, context):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    try:
        if 'kProtocol' in event:
            protocol = event['kProtocol']
        else:
            event['body'] = json.loads(event['body'])

        event_validation_graphql(event)

        response = graphql_query(event['body']['country'])

        print(response)
        return my_response(200, response)
    except Exception as e:
        logging.error(e)
        return my_response(400, str(e))


def graphql_query(country):
    try:
        headers_custom = {
            'Accept': 'application/json, */*',
            'Content-type': 'application/json'
        }

        url = 'https://countries.trevorblades.com'
        query = '{ country(code: \"' + country + '\") { name } }'

        response = requests.post(
            url,
            json={'query': query, 'variables': '{}'},
            headers=headers_custom
        )

        response_json = response.json()

        if response.status_code != 200:
            raise Exception('HTTP != 200')

        return response_json['data']
    except HTTPError as http_err:
        raise Exception(str(http_err))
    except Exception as err:
        raise Exception(str(err))
    return


def lambda_graphql(data):
    try:
        print(data)
        json = {
            'country': data,
        }

        url = os.environ["GQL_SAME"]

        response = requests.post(
            url,
            json=json,
            timeout=10,
            verify=False
        )

        if response.status_code != 200:
            # TODO better with url, size, data
            raise Exception('HTTP != 200')
        response_json = response.json()
        return response_json # ['data']
    except HTTPError as http_err:
        raise Exception(str(http_err))
    except Exception as err:
        raise Exception(str(err))
    return


def lambda_spawn(url, size, data):
    try:
        json = {
            'action': 'spawn',
            'bunch': {
                'size': size,
                'data': data
            }
        }

        response = requests.post(
            url,
            json=json,
            timeout=10,
            verify=False
        )

        if response.status_code != 200:
            # TODO better with url, size, data
            raise Exception('HTTP != 200')

        return 'a'
    except HTTPError as http_err:
        raise Exception(str(http_err))
    except Exception as err:
        raise Exception(str(err))
    return


def my_response(code, body):
    return {
        "statusCode": code,
        "body": json.dumps({'response': body})
    }


def reporter(event, context):
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    try:
        protocol = 'https'

        if 'kProtocol' in event:
            protocol = event['kProtocol']
        else:
            event['body'] = json.loads(event['body'])

        event_validation_reporter(event)

        if event['body']['bunch']['size'] > 1:
            url = "{}://{}{}".format(protocol, event['requestContext']['domainName'], event['requestContext']['path'])
            chunks = data_chunker(event['body']['bunch']['data'], int(event['body']['bunch']['size'] / 10))
            for i in chunks:
                print("spawn " + str(len(i)))
                lambda_spawn(url, len(i), i)
        else:
            # print(protocol + '://' + event['requestContext']['domainName'] + '/' + event['requestContext']['stage'] + '/' + event['requestContext']['resourcePath'])
            # print(event['body']['bunch']['data'][0])
            print(lambda_graphql(event['body']['bunch']['data'][0]))

        return my_response(200, "a")
    except Exception as e:
        logging.error(e)
        return my_response(400, str(e))
