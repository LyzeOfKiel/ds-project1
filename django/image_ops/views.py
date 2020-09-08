from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect

from .models import Image
from .utils import search, rgb_to_hls_scaled

from elasticsearch import Elasticsearch

import boto3
from botocore.client import Config

from colorthief import ColorThief

import os
import base64


def upload(request):
    pictures = 'pictures'

    s3 = boto3.resource(
        's3',
        endpoint_url='http://s3:9000/',
        aws_access_key_id='AKIAIOSFODNN7EXAMPLE',
        aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        config=Config(signature_version='s3v4'),
    )

    if s3.Bucket(pictures) not in s3.buckets.all():
        s3.create_bucket(Bucket=pictures)

    for file in request.FILES.getlist('files'):
        tmp_path = os.path.join(os.getcwd(), '/tmp_file')
        with open(tmp_path, 'wb+') as tmp:
            tmp.write(file.read())

        s3.Bucket(pictures).upload_file(tmp_path, file.name)

        color_thief = ColorThief(tmp_path)
        try:
            palette_rgb = color_thief.get_palette(color_count=10)
        except:
            print('error')

        os.remove(tmp_path)

    
        palette_hls = [rgb_to_hls_scaled(*c) for c in palette_rgb]

        es = Elasticsearch('es')
        body = {
            'bucket': pictures,
            'file_name': file.name,
            'colour_list': [{
                'h': c[0],
                'l': c[1],
                's': c[2],
            } for c in palette_hls]
        }
        r = es.index(index=pictures, body=body)
        assert r['result'] == 'created'

    return redirect('index')


def index(request):
    index = 'pictures'

    es = Elasticsearch('es')

    # es.indices.delete(index='pictures', ignore=[400, 404])

    mapping = {
        'mappings': {
            'properties': {
                'colour_list': {'type': 'nested'}
            }
        }
    }
    es.indices.create(index=index, body=mapping, ignore=400)

    # print('ALL')
    # print(es.search(body={
    #     'query': {
    #         'match_all': {}
    #     }
    # }, index=index)['hits']['hits'])

    template = loader.get_template('index.html')
    return HttpResponse(template.render({}, request))


def filter(request):
    s3 = boto3.resource(
        's3',
        endpoint_url='http://s3:9000/',
        aws_access_key_id='AKIAIOSFODNN7EXAMPLE',
        aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        config=Config(signature_version='s3v4'),
    )
    es = Elasticsearch('es')
    h = float(request.GET['h'])
    s = float(request.GET['s'])
    l = float(request.GET['l'])
    res = search(es, h, s, l)
    pictures = []
    for pic in res:
        file_name = pic['_source']['file_name']
        file_path = os.path.join(os.getcwd(), f'/tmp/{file_name}')
        # print(file_path)
        s3.Bucket('pictures').download_file(
            file_name,
            file_path
        )
        pictures.append({
            'name': file_name,
            'bytes': base64.b64encode(open(file_path, 'rb').read()).decode("utf-8") 
        })
    template = loader.get_template('filtered.html')
    return HttpResponse(template.render({
        'pictures': pictures
    }, request))
    # search(es, )
