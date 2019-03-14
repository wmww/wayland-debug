
class Enum:
    def __init__(self, **kwargs):
        self.map = {}
        for name, number in kwargs.items():
            self.map[number] = name
        self.bitwise = False
    def set_bitwise(self, val=True):
        self.bitwise = val
        return self
    def look_up(self, number):
        if self.bitwise:
            return [name for n, name in self.map.items() if number & n]
        elif number in self.map:
            return [self.map[number]]
        else:
            return []

enums = {
    ('wl_seat', 'capabilities', 0): Enum(
        pointer=1,
        keyboard=2,
        touch=4,
    ).set_bitwise(),
}

def look_up(type_name, message_name, arg_index, arg_value):
    key = (type_name, message_name, arg_index)
    if key in enums:
        return enums[key].look_up(arg_value)
    else:
        return None
