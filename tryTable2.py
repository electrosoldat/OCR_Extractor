import webbrowser, os 
import json 
import boto3
import io
from io import BytesIO
import sys
import csv
import re
import math
from PIL import Image, ImageDraw, ImageFont

def ShowBoundingBox(draw,box,width,height,boxColor):

	left = width * box['Left']
	top = height * box['Top']
	draw.rectangle([left,top, left + (width * box['Width']), top +(height *
	box['Height'])],outline=boxColor)

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

def main():
	bucket = 'invoicestc26'
	document = 'invoice1.PNG'

	s3_connection = boto3.resource('s3')
	s3_object = s3_connection.Object(bucket,document)
	s3_response = s3_object.get()
	stream = io.BytesIO(s3_response['Body'].read())
	image=Image.open(stream)

	client = boto3.client('textract')
	response = client.analyze_document(Document={'S3Object':{'Bucket':bucket,'Name' : document}}, FeatureTypes=["TABLES"])

	blocks = response['Blocks']
	width, height =image.size
	draw = ImageDraw.Draw(image)

	blocks_map = {}
	table_blocks = []
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
		blocks_map[block['Id']] = block
		if block['BlockType'] == "TABLE":
			table_blocks.append(block)

	for index, table in enumerate(table_blocks):

		rows = {}
		for relationship in table['Relationships']:
			if relationship['Type'] == 'CHILD':
				for child_id in relationship['Ids']:
					cell = blocks_map[child_id]
					if cell['BlockType'] == 'CELL':
						row_index = cell['RowIndex']
						col_index = cell['ColumnIndex']
						if row_index not in rows:
							# Create new row
							rows[row_index] = {}

						# get the text value
						rows[row_index][col_index] = get_text(cell,blocks_map)



	output_str = ""
	for row_index, cols in rows.items():
		for col_index, text in cols.items():
			output_str += text
			output_str += ","

		output_str += "\n"

	print(output_str)

	image.show()

if __name__ == '__main__':
	main()