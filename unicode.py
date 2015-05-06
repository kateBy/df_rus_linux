from binio import *

def patch_unicode_table(fn, off):
    upper_a_ya = [c for c in range(0x0410, 0x0430)]
    assert(len(upper_a_ya) == 0x20)
    ord_upper_a = int.from_bytes('А'.encode('cp1251'), 'little')
    fpoke4(fn, off+ord_upper_a*4, upper_a_ya)
    
    lower_a_ya = [c for c in range(0x0430, 0x0450)]
    assert(len(lower_a_ya) == 0x20)
    ord_lower_a = int.from_bytes('а'.encode('cp1251'), 'little')
    fpoke4(fn, off+ord_lower_a*4, lower_a_ya)
    
    upper_yo = 0x0401
    ord_upper_yo = int.from_bytes('Ё'.encode('cp1251'), 'little')
    fpoke4(fn, off+ord_upper_yo*4, upper_yo)
    
    lower_yo = 0x0451
    ord_lower_yo = int.from_bytes('ё'.encode('cp1251'), 'little')
    fpoke4(fn, off+ord_lower_yo*4, lower_yo)

def print_table(table):
    import struct
    template = struct.Struct("I" * 256)
    unpacked = template.unpack(table)
    str_template = ("0x%08X "*16 + "\n")*16

    print(str_template % unpacked)

def unicode_patch(old_fn, new_fn):

    unicode_table_start = [0x20, 0x263A, 0x263B, 0x2665, 0x2666, 0x2663, 0x2660, 0x2022]
    encoded_table = b""
    for char in unicode_table_start:
        encoded_table += char.to_bytes(4, 'little')

    data = open(old_fn, 'rb').read()

    offset = data.find(encoded_table)
    if offset == -1:
        print("NO UNICODE TABLE")
        exit()

    from io import BytesIO

    fn = BytesIO()
    fn.write(data)

    fn.seek(offset )
    table1 = fn.read(256 * 4)

    patch_unicode_table(fn, offset)

    fn.seek(offset)
    table2 = fn.read(256 * 4)

    open(new_fn, 'wb').write(fn.getvalue())


