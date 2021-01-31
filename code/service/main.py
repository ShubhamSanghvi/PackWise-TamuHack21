from flask import Flask, render_template
from flask import request, jsonify

from flask_cors import CORS, cross_origin
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


import io
import os
import base64

# Imports the Google Cloud client library
from google.cloud import vision

# Instantiates a client
client = vision.ImageAnnotatorClient()

# The name of the image file to annotate
dir_name = os.path.abspath('D:/Personal/chaand_ki_khoj/in_the_end/Datathon2020/TamuHack21/Images')

keywords = {}
keywords_filename = "keywords.txt"
with open(keywords_filename, 'r') as keywords_file: # open in readonly mode
    lines = keywords_file.readlines()
    for line in lines:
        words = line.split(",")
        if len(words) > 1:
            keywords[words[0]] = words[1].strip()

category = {}
category_filename = "category.txt"
with open(category_filename, 'r') as category_file: # open in readonly mode
    lines = category_file.readlines()
    for line in lines:
        words = line.split(",")
        words = [word.strip() for word in words]
        if len(words) > 3:
            category[words[1]] = words[2:]

broad = {}
label_filename = "label.txt"
with open(label_filename, 'r') as label_file: # open in readonly mode
    lines = label_file.readlines()
    for line in lines:
        words = line.split(",")
        if len(words) > 1:
            broad[words[0]] = words[1].strip()



@app.route("/")
@cross_origin()
def homepage():
    return render_template("index.html", title="HOME PAGE")

@app.route("/docs")
@cross_origin()
def docs():
    return render_template("index.html", title="docs page")

@app.route("/about")
@cross_origin()
def about():
    return render_template("index.html", title="about page")

@app.route('/api',methods=['POST'])
@cross_origin()
def predict():
    # Get the data from the POST request.
    data = request.get_json(force=True)

    output = {"status":"false"}

    # Loads the image into memory
    # with io.open(file_name, 'rb') as image_file:
    print("--------------------------------------------------")
    try:
        # content = image_file.read()
        # content = 
        # file1 = open("D:/Personal/chaand_ki_khoj/in_the_end/Datathon2020/TamuHack21/Images/calculator.txt","r+")
        # content = binascii.a2b_base64()
        img_str = data['image']
        imgdata = base64.b64decode(img_str.split(",")[1])
        # filename = 'some_image.jpg'  # I assume you have a way of picking unique filenames
        # with open(filename, 'wb') as f:
        #     f.write(imgdata)

        # image_file = open(filename,'rb')
        # content = image_file.read()
        # file1.close()

        # csv_line = [filename.split("\\")[-1]]
        csv_line = []
        image = vision.Image(content=imgdata)
        
        response = client.text_detection(image=image)
        texts = response.text_annotations

        text_words = [text.description for text in texts]
        # first one is a combined text already but with new lines
        text_combined = " ".join(text_words[1:])
#            print(text_combined)
        csv_line.append("TXT-" + text_combined)

        if response.error.message:
            raise Exception(
                '{}\nFor more info on error messages, check: '
                'https://cloud.google.com/apis/design/errors'.format(
                    response.error.message))

        
        objects = client.object_localization(
            image=image).localized_object_annotations
        
        item_desc = []
#            print('Number of objects found: {}'.format(len(objects)))
        for object_ in objects:
#                print('{} (confidence: {})'.format(object_.name, object_.score))
            csv_line.append("OBJ-"+ object_.name + " (" +"{:.2f}".format(object_.score) + ")")
            for obj_name in object_.name.split(" "):
                item_desc.append((obj_name.lower(), object_.score))
            
            # csv_line.append(str(object_.score))

        # Performs label detection on the image file
        response = client.label_detection(image=image)
        labels = response.label_annotations

#            print('Labels:')
        for label in labels:
#                print(label.description, label.score)
            csv_line.append(label.description + " (" + "{:.2f}".format(label.score)+ ")")
            for lbl_name in label.description.split(" "):
                item_desc.append((lbl_name.lower(), label.score))
            # csv_line.append(str(label.score))

        
        ## code to checkif we are doing this
        item_desc = sorted(item_desc, key= lambda x: x[1], reverse=True)
        notAllowed = False
        result = ["NA", "yes","yes","You are good to go.","You are good to go.","https://www.tsa.gov/travel/security-screening/whatcanibring/all?combine=&page=2"]

        if data['source'] == data['destination']:
            for lbl,_ in item_desc:
                if lbl in ('seeds','plant','seed','plants'):
                    result = [lbl] + category['seed']
                    notAllowed = True
                    print(result)
                    break
        
        if not notAllowed:
            for lbl,_ in item_desc:
                if lbl in keywords:
                    result = [lbl] + category[keywords[lbl]]
                    notAllowed = True
                    print(result)
                    break
        
        
        if not notAllowed:
            for lbl,_ in item_desc:
                if lbl in broad:
                    result = [lbl] + category[broad[lbl]]
                    notAllowed = True
                    print(result)
                    break
                
    
        # myCsvRow = ",".join(csv_line)
        # myCsvRow += "\n"
        # myCsvRow = ",".join(result) + "," + myCsvRow
        # with open('final.csv','a') as fd:
        #     fd.write(myCsvRow)

        print("DONE")
        isError = False
    except Exception as ex:
        result = ["NA", "err","err","ERROR","ERROR","https://www.tsa.gov/travel/security-screening/whatcanibring/all?combine=&page=2"]
        isError = True
        print("ERROR", ex)


    output["debugMatchLabel"] = result[0]
    output["isAllowedCarry"] = result[1]
    output["isAllowedCheckin"] = result[2]
    output["descriptionCabin"] = result[3]
    output["descriptionCheckin"] = result[4]
    output["moreInfoLink"] = result[5]
    output["status"] = str(not isError)

    return jsonify(output)


if __name__ == "__main__":
    app.run(debug=True)