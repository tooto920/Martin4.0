with open('app/gui/theme.py', 'r', encoding='utf-8') as f:
    c = f.read()
old = "    border-radius: 0px;\n}}\n'''" + "p"
new = "    border-radius: 0px;\n}}\n" + '"""' + "\n\nprint('theme.py written')"
c = c.replace(old, new)
with open('app/gui/theme.py', 'w', encoding='utf-8') as f:
    f.write(c)
print('Fixed')
