import os
from flask import Flask, render_template, request,send_file, redirect, url_for,session
from flask.helpers import send_file
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from flask_wtf.file import FileAllowed

import nltk
nltk.download('punkt')

import cv2 as cv
import pytesseract
import numpy as np
import pandas as pd
from nltk.tokenize import word_tokenize
import string
import uuid




pytesseract.pytesseract.tesseract_cmd= r'C:\Program Files\Tesseract-OCR\tesseract.exe'
#  pytesseract.pytesseract.tesseract_cmd= '/app/.apt/usr/bin/tesseract'
# tesseract_config = r'--oem 3 --psm 6'
# boxes = pytesseract.image_to_data(img,output_type=pytesseract.Output.DICT, config=tesseract_config, lang='eng')


text = ""
f_name = ""
l = []

def text_recog(file):
    tesseract_config = r'--oem 3 --psm 6'
    d = pytesseract.image_to_data(file,output_type=pytesseract.Output.DICT, config=tesseract_config, lang='eng')

    # custom_config = r'-c preserve_interword_spaces=1 --oem 1 --psm 1 -l eng+ita'
    # d = pytesseract.image_to_data(file, config=custom_config, output_type=pytesseract.Output.DICT)
    return (d)


def write_download_file(d):

    df = pd.DataFrame(d)

    df1 = df[(df.conf!='-1')&(df.text!=' ')&(df.text!='')]
    sorted_blocks = df1.groupby('block_num').first().sort_values('top').index.tolist()
    for block in sorted_blocks:
        curr = df1[df1['block_num']==block]
        sel = curr[curr.text.str.len()>3]
        char_w = (sel.width/sel.text.str.len()).mean()
        prev_par, prev_line, prev_left = 0, 0, 0
        text = ''
        for ix, ln in curr.iterrows():
            # add new line when necessary
            if prev_par != ln['par_num']:
                text += '\n'
                prev_par = ln['par_num']
                prev_line = ln['line_num']
                prev_left = 0
            elif prev_line != ln['line_num']:
                text += '\n'
                prev_line = ln['line_num']
                prev_left = 0

            added = 0  # num of spaces that should be added
            if ln['left']/char_w > prev_left + 1:
                added = int((ln['left'])/char_w) - prev_left
                text += ' ' * added 
            text += ln['text'] + ' '
            prev_left += len(ln['text']) + added + 1
        text += '\n'
        l.append(text)

    s = ''.join(l)

    # filename = str(uuid.uuid4())
    filename = uuid.uuid4().hex
    global f_name
    f_name=filename + '.txt'
    # print(f_name)
    
    text_file = open(f_name, "w")
    # if os.stat('sample.txt').st_size == 0:
    #     print('File is empty')
    text_file.write(s)
    text_file.close()


app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
basedir = os.path.abspath(os.path.dirname(__file__))
# app.config['DOWNLOAD_DEST'] = os.path.join(basedir, 'uploads') 

 
class UploadForm(FlaskForm):
    photo = FileField('image',validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Get Text')



@app.route('/',methods=['GET','POST'])
def upload_file():
    form = UploadForm()
    if form.validate_on_submit():
        
  
        file = request.files['photo'].read()

        npimg = np.fromstring(file, np.uint8)
        image = cv.imdecode(npimg,cv.IMREAD_COLOR)

        # print(pytesseract.get_tesseract_version())
        data = text_recog(image)
        


        write_download_file(data)

        
      
        res = list(data.values())
        global text 
        text = res[11]
        text = str(text)
        tokens = word_tokenize(text)
        table = str.maketrans('', '', string.punctuation)
        stripped = [w.translate(table) for w in tokens]
        words = [word for word in stripped if word.isalpha()]
        listToStr = ' '.join([str(elem) for elem in words])
        text = listToStr
        # form.text.data = text
    
    return render_template('index.html',form=form,text=text)





@app.route('/download')
def download_file():

    file = f_name
           
    return send_file(file,as_attachment=True)



@app.route('/clear-session')
def clear_session():

    global text
    text = ""

    session.clear()
    return render_template('clear_session.html',text = text)
            




if __name__ == '__main__':
    app.run(debug=True)
