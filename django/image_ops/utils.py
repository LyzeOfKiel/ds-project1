from colorsys import rgb_to_hls


def rgb_to_hls_scaled(r, g, b):
    (h, l, s) = rgb_to_hls(r/255, g/255, b/255)
    return h * 360, l * 100, s * 100


def search(es, h, s, l):
    delta = 0.3
    QUERY = {
        'nested': {
            'path': 'colour_list',
            'score_mode': 'sum',
            'query': {
                'function_score': {
                    'query': {
                        'nested': {
                            'path': 'colour_list',
                            'query': {
                                'bool': {
                                    'must': [
                                        {
                                            'range': {
                                                'colour_list.h': {
                                                    'gte': h*(1-delta),
                                                    'lte': h*(1+delta)
                                                }
                                            }
                                        },
                                        {
                                            'range': {
                                                'colour_list.s': {
                                                    'gte': s*(1-delta),
                                                    'lte': s*(1+delta)
                                                }
                                            }
                                        },
                                        {
                                            'range': {
                                                'colour_list.l': {
                                                    'gte': l*(1-delta),
                                                    'lte': l*(1+delta)
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    'boost_mode': 'replace',
                    'functions': [
                        {
                            'exp': {
                                'colour_list.h': {
                                    'origin': h,
                                    'offset': 1,
                                    'scale': 2
                                }
                            }
                        },
                        {
                            'exp': {
                                'colour_list.s': {
                                    'origin': s,
                                    'offset': 2,
                                    'scale': 4
                                }
                            }
                        },
                        {
                            'exp': {
                                'colour_list.l': {
                                    'origin': l,
                                    'offset': 2,
                                    'scale': 4
                                }
                            }
                        }
                    ]
                }
            }
        }
    }

    query_conf = {
        'size': 10,
        'query': QUERY
    }
    res = es.search(body=query_conf, index='pictures')['hits']['hits']
    for o in res:
        print(o['_score'], o['_source']['file_name'])
    print(res)
    return res


