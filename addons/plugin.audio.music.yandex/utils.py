def get_parameters(source):
    params = {}
    if not source:
        return params
    source = source.replace('?', '')
    for item in source.split('&'):
        key, value = item.split('=')
        params[key] = value
    return params
