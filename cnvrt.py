import os
import base64


path = "../cas"


filelist = os.listdir(path)

for file in filelist:
    base64_bytes = file.encode("ascii")
    sample_string_bytes = base64.b64decode(base64_bytes)
    sample_string = sample_string_bytes.decode("ascii")
    print(sample_string)
    os.rename(path + '/' + file , path + '/' + sample_string)

filelist = os.listdir(path)
    
filelist = sorted(filelist, key=lambda x: int(os.path.splitext(x)[0]))

yon = open("../görev.txt", 'w')

for file in filelist:
    content = open(path + "/" + file).read()
    text = "".join(chr(int(s, 2)) for s in  content.split())
    print(text)
    yon.write(text)
    

yon.close()