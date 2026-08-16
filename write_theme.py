import pathlib
p = pathlib.Path('app/gui/theme.py')
text = p.read_text(encoding='utf-8')
text = text.rstrip()
fix = "'''" + chr(10) + 'print("theme.py written")' + chr(10)
if not text.endswith("'''"):
    p.write_text(text + fix, encoding='utf-8')
    print('Fixed theme.py')
else:
    print('Already closed')
