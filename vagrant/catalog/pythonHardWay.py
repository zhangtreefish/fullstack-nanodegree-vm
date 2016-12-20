# import pydoc
from sys import argv

script, user_name = argv
prompt = '&'

print ('Hi %s, I am the %s script.') %(user_name,script)
print('Do you like me %s?') % user_name  # this does the asking
likes = raw_input(prompt)  # this collects the input
live = raw_input('Where do you live?')
print('So you live at %r') %live

print '''
Alright %s from %s, so you said %s about liking me.
''' %(user_name,live,likes)
