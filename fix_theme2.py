with open('app/gui/theme.py', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('}}' + chr(39)*3, '}}' + chr(34)*3)
with open('app/gui/theme.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Fixed')
