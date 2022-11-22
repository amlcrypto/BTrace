"""Utils module"""


def parse_message(data: str) -> str:
    data_items = data.split('\n')
    data_dict = {}
    for item in data_items:
        row = item.split(': ')
        data_dict.update({row[0]: row[1]})

    sp = data_dict.get('Sender').rsplit('>', 2)[1].split(' ')
    if len(sp) == 1:
        address = data_dict.get('Sender').split('"')[1].rsplit('/', 1)[1]
    else:
        address = data_dict.get('Receiver').split('"')[1].rsplit('/', 1)[1]
    return address

