'''
@author: admin
'''

# pip install pytest-aio

import asyncio


async def test_async():
	print('Hello ...')
	await asyncio.sleep(10)
	print('... World!')
	assert False

class Scenario(object):
	'''
	classdocs
	'''


	def __init__(self):
		'''
		Constructor
		'''
		
		
	def run(self):
		asyncio.run(test_async())