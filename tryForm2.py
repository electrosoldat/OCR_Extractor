import boto3
import sys
import re
import json
import io
from io import BytesIO
import math
from PIL import Image, ImageDraw, ImageFont

def ShowBoundingBox(draw,box,width,height,boxColor):

	left = width * box['Left']
	top = height * box['Top']
	draw.rectangle([left,top, left + (width * box['Width']), top +(height *
	box['Height'])],outline=boxColor)

def find_value_block(key_block, value_map):
	for relationship in key_block['Relationships']:
		if relationship['Type'] == 'VALUE':
			for value_id in relationship['Ids']:
				value_block = value_map[value_id]
	return value_block

def get_text(result, blocks_map):
	text = ''
	if 'Relationships' in result:
		for relationship in result['Relationships']:
			if relationship['Type'] == 'CHILD':
				for child_id in relationship['Ids']:
					word = blocks_map[child_id]
					if word['BlockType'] == 'WORD':
						text += word['Text'] + ' '
	return text

def get_kv_relationship(key_map,value_map,block_map):
	kvs = {}
	for block_id, key_block in key_map.items():
		value_block = find_value_block(key_block, value_map)
		key = get_text(key_block, block_map)
		val = get_text(value_block, block_map)
		kvs[key] = val
	return kvs

def print_kvs(kvs):
	for key, value in kvs.items():
		print(key, ":", value)

def search_value(kvs,search_key):
	for key,value in kvs.items():
		if re.search(search_key, key, re.IGNORECASE):
			return value

def main():
	bucket = 'invoicestc26'
	document = 'hook_invoice1.PNG'
	s3_connection = boto3.resource('s3')
	s3_object = s3_connection.Object(bucket,document)
	s3_response = s3_object.get()
	stream = io.BytesIO(s3_response['Body'].read())
	image=Image.open(stream)
	client = boto3.client('textract')
	response = client.analyze_document(Document={'S3Object':{'Bucket':bucket,'Name' : document}}, FeatureTypes=["FORMS"])

	# Get the text blocks
	blocks = response['Blocks']
	width, height =image.size
	draw = ImageDraw.Draw(image)

	# get key and value maps
	key_map = {}
	value_map = {}
	block_map = {}
	for block in blocks:
		draw=ImageDraw.Draw(image)
		if block['BlockType'] == "KEY_VALUE_SET":
			if block['EntityTypes'][0] == "KEY":
				ShowBoundingBox(draw, block['Geometry']['BoundingBox'],width,height,'red')
			else:
 				ShowBoundingBox(draw, block['Geometry']['BoundingBox'],width,height,'green')

		if block['BlockType'] == 'TABLE':
			ShowBoundingBox(draw, block['Geometry']['BoundingBox'],width,height,'blue')
		if block['BlockType'] == 'CELL':
			ShowBoundingBox(draw, block['Geometry']['BoundingBox'],width,height,'yellow')
		block_id = block['Id']
		block_map[block_id] = block
		if block['BlockType'] == "KEY_VALUE_SET":
			if 'KEY' in block['EntityTypes']:
				key_map[block_id] = block
			else:
				value_map[block_id] = block

	# get key value relationships
	kvs = get_kv_relationship(key_map, value_map, block_map)

	print("\n\n== FOUND KEY : VALUE pairs ===\n")
	print_kvs(kvs)

	image.show()

	# Start searching a key value
	while input('\n Do You Want To Search A Value For A Key? (enter "n" for exit) ') != 'n':
		search_key = input('\n Enter a search key:')
		print('The value is:', search_value(kvs, search_key))

if __name__ == '__main__':
	main()