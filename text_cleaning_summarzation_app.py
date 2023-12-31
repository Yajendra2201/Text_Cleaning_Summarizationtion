import streamlit as st
import PyPDF2
import docx
import requests
from bs4 import BeautifulSoup
import re
import unicodedata
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io
import textwrap
import string
# [Include all your text cleaning functions here]
def lowercase(textString):
    textString = textString.lower()
    return textString

def specialpunctNLP(textString):
    textString = re.sub(r'\W+',' ',textString)
    return textString

def specialpunct(textString, keep_punctuations=".?,!;:"):
    remove_punct_map = str.maketrans('', '', ''.join(ch for ch in string.punctuation if ch not in keep_punctuations))
    textString = textString.translate(remove_punct_map)
    return textString

def extraspace(textString):
    textString = ' '.join(textString.split())
    return textString

def sentence_case(textString):
    textString = textString.title()
    return textString

def remove_special_accent(textString):
    textString = unicodedata.normalize('NFKD',textString).encode('ASCII','ignore').decode('UTF-8')
    return textString

def remove_html_tags(textString):
    soup = BeautifulSoup(textString,'html.parser')
    text = soup.get_text()
    return text

def remove_urls(textString):
    textString = re.sub(r"(http|https)?:S*","",textString)
    return textString

def remove_emojis(textString):
    emoj = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
                      "]+", re.UNICODE)
    textString = re.sub(emoj, '', textString)
    return textString

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    return text
 
 
def create_pdf_with_text(text, output_pdf_path, x=72, y=720, font_name="Helvetica", font_size=12, line_spacing=14, max_width=8*inch):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    can.setFont(font_name, font_size)

    # Wrap the text to fit within the specified width
    wrapped_text = textwrap.fill(text, width=int(max_width/(font_size*0.6)))
    lines = wrapped_text.split('\n')

    # Draw each line
    for line in lines:
        can.drawString(x, y, line)
        y -= line_spacing

    can.save()

    packet.seek(0)
    with open(output_pdf_path, 'wb') as file:
        file.write(packet.getvalue())

def clean_text(textString, for_nlp=False):
    l = lowercase(textString)
    a = specialpunctNLP(l) if for_nlp else specialpunct(l)
    t = extraspace(a)
    y = sentence_case(t) if not for_nlp else t
    i = remove_special_accent(y)
    p = remove_html_tags(i)
    k = remove_urls(p)
    n = remove_emojis(k)
    return n


# Function to extract text from a DOCX file
def extract_text_from_docx(docx_file):
    doc = docx.Document(docx_file)
    return '\n'.join([paragraph.text for paragraph in doc.paragraphs])

# Function to extract text from a URL
def extract_text_from_url(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup.get_text()

def local_css(file_name):
    with open(file_name, "r") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Apply the custom CSS
local_css("style.css")

# Set page configuration
st.set_page_config(layout="wide", page_title="Advanced Text Cleaning App")

# Streamlit interface setup
st.title('Advanced Text Cleaning App')

# Columns for layout
col1, col2 = st.columns(2)

with col1:
    # User choice for type of text cleaning
    text_cleaning_choice = st.radio("Select the type of text cleaning", ('Normal Text Cleaning', 'NLP Task'))

with col2:
    # Choose between text input, PDF upload, DOCX upload, or URL input
    input_choice = st.radio("Choose Input Type", ('Paste Text', 'Upload PDF', 'Upload DOCX', 'Enter URL'))

# Process and show text
def process_and_show_text(text):
    cleaned_text = clean_text(text,for_nlp=text_cleaning_choice == 'NLP Task')
    st.text_area("Cleaned Text", cleaned_text, height=250)

# Process and download PDF
def process_and_download_pdf(uploaded_file):
    with open('uploaded_file.pdf', 'wb') as f:
        f.write(uploaded_file.getbuffer())
    extracted_text = extract_text_from_pdf('uploaded_file.pdf')
    processed_text = clean_text(extracted_text)
    output_pdf_path = 'cleaned_output.pdf'
    create_pdf_with_text(processed_text, output_pdf_path)
    st.download_button(label="Download Cleaned PDF",
                       data=open(output_pdf_path, "rb"),
                       file_name="cleaned_output.pdf",
                       mime="application/octet-stream")

if input_choice == 'Paste Text':
    text_input = st.text_area("Paste your text here:")
    if st.button("Clean Text"):
        if text_input:
            cleaned_text = clean_text(text_input, for_nlp=text_cleaning_choice == 'NLP Task')
            st.text_area("Cleaned Text", cleaned_text, height=250)
        else:
            st.warning("Please paste some text to clean.")

elif input_choice == 'Upload PDF':
    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
    if st.button("Process PDF"):
        if uploaded_file:
            process_and_download_pdf(uploaded_file)
        else:
            st.warning("Please upload a PDF file.")

elif input_choice == 'Upload DOCX':
    uploaded_file = st.file_uploader("Upload a DOCX file", type=["docx"])
    if st.button("Process DOCX"):
        if uploaded_file:
            extracted_text = extract_text_from_docx(uploaded_file)
            process_and_show_text(extracted_text)
        else:
            st.warning("Please upload a DOCX file.")

elif input_choice == 'Enter URL':
    url_input = st.text_input("Enter the URL:")
    if st.button("Extract and Clean Text from URL"):
        if url_input:
            extracted_text = extract_text_from_url(url_input)
            process_and_show_text(extracted_text)
        else:
            st.warning("Please enter a URL.")

