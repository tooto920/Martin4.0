with open('config/config.yaml', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('    - "C:\\Users\\lukas\\Documents"', "    - 'C:\\Users\\lukas\\Documents'")
c = c.replace('    - "C:\\Users\\lukas\\Downloads"', "    - 'C:\\Users\\lukas\\Downloads'")
c = c.replace('    - "C:\\Users\\lukas\\Desktop"', "    - 'C:\\Users\\lukas\\Desktop'")
with open('config/config.yaml', 'w', encoding='utf-8') as f:
    f.write(c)
print('Fixed')
