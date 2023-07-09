import base64
import os
import openai
from urllib.parse import quote as urlquote
import whisper
from datetime import timedelta

from flask import Flask, send_from_directory
import dash
from dash import Dash, html, dcc, callback, Input, Output,State
from dash.exceptions import PreventUpdate



UPLOAD_DIRECTORY = "/Users/sfyen/GDisk/Learning/pythonLearn/AIGO-2023/files"
openai.api_key = os.getenv("OPENAI_KEY_AIGO23")

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)


# Normally, Dash creates its own Flask server internally. By creating our own,
# we can create a route for downloading files directly:
server = Flask(__name__)
app = dash.Dash(server=server,title='英文文摘中文摘要網')



def Eng2Chi(text):
    #openai.api_key = os.getenv("OPENAI_KEY_AIGO23")
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"請給我下面文章的繁體中文摘要: {text}",
        temperature=0.8,
        max_tokens=600,
        #top_p=1,
        #frequency_penalty=0,
        #presence_penalty=0
    )
    translation = response.choices[0].text.strip()
    return(translation)

def Eng22Chi(text):
    #openai.api_key = os.getenv("OPENAI_KEY_AIGO23")
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"Translate English into 繁體中文: {text}",
        temperature=0.5,max_tokens=100,
        top_p=1,frequency_penalty=0,presence_penalty=0
    )
    translation = response.choices[0].text.strip()
    return(translation)

def transcribe_audio(file):
    model = whisper.load_model("base")
    #model = whisper.load_model("large")
    # Change this to your desired model
    filepath='./files/'+file
    print("will start to model the file")
    print(filepath)
    transcribe = model.transcribe(filepath,fp16=False)
    segments = transcribe['segments']

    for segment in segments:
        startTime = str(0)+str(timedelta(seconds=int(segment['start'])))+',000'
        endTime = str(0)+str(timedelta(seconds=int(segment['end'])))+',000'
        text = segment['text']
        segmentId = segment['id']+1
        textChi = Eng22Chi(text)
        print(text,textChi)
        segment     = f"{segmentId}\n{startTime} --> {endTime}\n{text[1:] if text[0] == ' ' else text}\n\n"
        segment_Chi = f"{segmentId}\n{startTime} --> {endTime}\n{text[1:] if text[0] == ' ' else text}{textChi[1:] if textChi[0] == ' ' else textChi}\n\n"
        try:
            srtFilename=file.split(".")[0]+".srt"
            srtFilename_Chi=file.split(".")[0]+"-Chi.srt"
        except:
            srtFilename='result.srt'
            srtFilename_Chi='result2.srt'
        with open('./files/'+srtFilename, 'a', encoding='utf-8') as srtFile:
            srtFile.write(segment)
        with open('./files/'+srtFilename_Chi, 'a', encoding='utf-8') as srtFileChi:
            srtFileChi.write(segment_Chi)
    print("End of the segment.")
    return srtFilename,srtFilename_Chi
    #return srtFilename

@server.route("/Users/sfyen/GDisk/Learning/pythonLearn/AIGO-2023/<path:path>")
def download(path):
    """Serve a file from the upload directory."""
    return send_from_directory(UPLOAD_DIRECTORY, path, as_attachment=True)


app.layout = html.Div([
    html.H1('OpenAI 作業-英文文稿-中文結論轉換頁面'),
    dcc.Textarea(
        id='textarea-input',
        value='請清除此行，並在這邊輸入英文文章,輸入完畢請按submit\n',
        style={'width': '45%', 'height': 300, 'margin-left':'3%',},
    ),
    html.Div(
        id='textarea-output',
        style={'whiteSpace': 'pre-line','width': '45%', 'height': 300,
               'float':'right', 'border-style':'solid','margin-right':'3%',},
    ),
    html.H6('--貼上文章後，請按下下面轉換'),
    html.Button('轉換', id='textarea-button', n_clicks=0),
    html.H2(''),
    html.H2('-----App 2, upload MP3 and generation the text -------'),
    #dcc.Upload(html.Button('Upload File'),id='upload-data',),
    html.H1("File Browser"),
    html.H2("Upload"),
    dcc.Upload( id="upload-data",
        children=html.Div(["Drag and drop or click to select a file to upload."]),
        style={
                "width": "90%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            multiple=True,
        ),
    html.H2("File List"),
    html.Ul(id="file-list"),
    ],
    #style={"max-width": "500px"},
)


def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), "wb") as fp:
        fp.write(base64.decodebytes(data))


def uploaded_files():
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(UPLOAD_DIRECTORY):
        path = os.path.join(UPLOAD_DIRECTORY, filename)
        if os.path.isfile(path):
            files.append(filename)
    return files


def file_download_link(filename):
    """Create a Plotly Dash 'A' element that downloads a file from the app."""
    location = "/Users/sfyen/GDisk/Learning/pythonLearn/AIGO-2023/{}".format(urlquote(filename))
    return html.A(filename, href=location)


@app.callback(
    Output("file-list", "children"),
    [Input("upload-data", "filename"), Input("upload-data", "contents")],
)
def update_output(uploaded_filenames, uploaded_file_contents):
    """Save uploaded files and regenerate the file list."""

    if uploaded_filenames is not None and uploaded_file_contents is not None:
        for name, data in zip(uploaded_filenames, uploaded_file_contents):
            save_file(name, data)
            #print(name)
            #transcribe_audio(name)
        print(name)
        transcribe_audio("test.mp3")
    files = uploaded_files()
    if len(files) == 0:
        return [html.Li("No files yet!")]
    else:
        return [html.Li(file_download_link(filename)) for filename in files]


@callback(
    Output('textarea-output', 'children'),
    Input('textarea-button', 'n_clicks'),
    State('textarea-input', 'value')
)
def update_output(n_clicks, value):
    if n_clicks > 0:
        print("Start The AI transfrom")
        a=Eng2Chi(value)
        print(a)
        #return 'You have entered: \n{}\t{}'.format(value,a)
        return '中文摘要是: \n{}'.format(a)

if __name__ == "__main__":
    app.run_server(debug=True,host='0.0.0.0',port='8054')
