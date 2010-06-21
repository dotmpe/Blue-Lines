test(__config_list__) and \
configList [
    [ include('breve/xml/config', {'__config__':a}) for a in __config_list__]
]
# vim:ft=python:
