import traceback
try:
    compile(open('backend/app/services/pipeline.py', encoding='utf-8').read(), 'pipeline.py', 'exec')
    print('No syntax errors!')
except SyntaxError as e:
    print('SYNTAX ERROR ON LINE', e.lineno)
    print('TEXT:', e.text)
