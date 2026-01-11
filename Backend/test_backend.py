'''import requests

text_notice = {
    "text": "You are hereby informed that due to non-payment of rent for the months of August and September, an amount of ₹45,000 is pending. If the payment is not made within 20 days from the receipt of this notice, appropriate legal action shall be initiated."
}

response = requests.post("http://127.0.0.1:5000/analyze", json=text_notice)
print("TEXT NOTICE RESPONSE:")
print(response.json())


pdf_file_path = r"C:\Users\Sricharani Vemparala\Documents\SampleLegalNotice1.pdf"  # Replace with your PDF path

with open(pdf_file_path, "rb") as f:
    files = {"file": f}
    response = requests.post("http://127.0.0.1:5000/analyze-pdf", files=files)

print("\nPDF NOTICE RESPONSE:")
print(response.json())
'''