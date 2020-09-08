from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect

from .utils import search, rgb_to_hls_scaled

from elasticsearch import Elasticsearch

from minio import Minio
from minio.error import (
    BucketAlreadyExists,
    BucketAlreadyOwnedByYou
)

from colorthief import ColorThief

import os
import json


BUCKET_NAME = 'pictures'
ANON_READ_ONLY_POLICY = json.dumps({
  'Version': '2012-10-17',
  'Statement': [
    {
      'Sid': 'PublicRead',
      'Effect': 'Allow',
      'Principal': '*',
      'Action': ['s3:GetObject', 's3:GetObjectVersion'],
      'Resource': [f'arn:aws:s3:::{BUCKET_NAME}/*']
    }
  ]
})


def initS3():
    return Minio(
        's3:9000',
        access_key='AKIAIOSFODNN7EXAMPLE',
        secret_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        secure=False,
    )


def upload(request):
    s3 = initS3()

    try:
        s3.make_bucket(BUCKET_NAME)
        s3.set_bucket_policy(BUCKET_NAME, ANON_READ_ONLY_POLICY)
    except BucketAlreadyExists:
        pass
    except BucketAlreadyOwnedByYou:
        pass

    for file in request.FILES.getlist('files'):
        tmp_path = os.path.join(os.getcwd(), '/tmp_file')
        with open(tmp_path, 'wb+') as tmp:
            tmp.write(file.read())

        s3.fput_object(BUCKET_NAME, file.name, tmp_path)

        color_thief = ColorThief(tmp_path)
        try:
            palette_rgb = color_thief.get_palette(color_count=10)
        except:
            print('error')

        os.remove(tmp_path)

        palette_hls = [rgb_to_hls_scaled(*c) for c in palette_rgb]

        es = Elasticsearch('es')
        body = {
            'bucket': BUCKET_NAME,
            'file_name': file.name,
            'colour_list': [{
                'h': c[0],
                'l': c[1],
                's': c[2],
            } for c in palette_hls]
        }
        r = es.index(index=BUCKET_NAME, body=body)
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

    template = loader.get_template('index.html')
    return HttpResponse(template.render({}, request))


def filter(request):
    s3 = initS3()

    es = Elasticsearch('es')
    h = float(request.GET['h'])
    s = float(request.GET['s'])
    l = float(request.GET['l'])
    res = search(es, h, s, l)
    pictures = []
    for pic in res:
        file_name = pic['_source']['file_name']
        file_path = os.path.join(os.getcwd(), f'/tmp/{file_name}')

        s3.fget_object(BUCKET_NAME, file_name, file_path)

        pictures.append({
            'name': file_name,
        })
    template = loader.get_template('filtered.html')
    return HttpResponse(template.render({
        'pictures': pictures
    }, request))
