import sys

def append_to_file(filename, content_file):
    with open(content_file, 'r', encoding='utf-8') as f_in:
        content = f_in.read()
    with open(filename, 'a', encoding='utf-8') as f_out:
        f_out.write(content)

if __name__ == '__main__':
    append_to_file(sys.argv[1], sys.argv[2])
