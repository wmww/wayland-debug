import gdb

def main(matcher):
    gdb.execute('set python print-stack full')
    print('GDB main')
