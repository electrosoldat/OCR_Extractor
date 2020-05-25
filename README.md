# OCR_Extractor
This project is an OCR-based structured text extractor.

The main goal is to detect and extract useful information from scanned invoices/bills, in order to convert them into digital format, for easy storage, accessibility and transfer.
___________________________________________________________________________________________________________________________________________

* This utilises the AWS Textract service, to detect all the text/data present in the image of the invoices.
* The AWS Textract returns a JSON response.
* The JSON response is used to get the relevant data, out of all the data detected.

* Also, the main highlight of this project is that it is able to successfully detect tables and key-value pairs present.
