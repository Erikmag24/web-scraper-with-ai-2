from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from translator import translate_text, get_available_languages
from web_scraper import scrape_and_process
import config
import os
import logging
import secrets
from ai_models import send_request_to_ai  # Importa la funzione per gestire la richiesta AI
from datetime import datetime  # Importa datetime per l'anno corrente

app = Flask(__name__)

# Set the secret key
app.config['SECRET_KEY'] = secrets.token_hex(16)

# Configure logging
logging.basicConfig(filename='app.log', level=logging.DEBUG)

# Configure upload folder
UPLOAD_FOLDER = os.path.abspath('uploads')
ALLOWED_EXTENSIONS = {'xlsx', 'docx', 'webm', 'wav', 'mp3'}  # Added audio file extensions
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template(
        'index.html',
        languages=get_available_languages(),
        search_engines=config.SEARCH_ENGINES,
        default_process_type='audio'  # Add a default process type for audio
    )

@app.route('/config', methods=['GET', 'POST'])
def config_page():
    if request.method == 'POST':
        # Update config with form data
        config.GPT_API_URL = request.form.get('GPT_API_URL', config.GPT_API_URL)
        config.GPT_API_KEY = request.form.get('GPT_API_KEY', config.GPT_API_KEY)
        config.OLLAMA_API_URL = request.form.get('OLLAMA_API_URL', config.OLLAMA_API_URL)
        config.COHERE_API_URL = request.form.get('COHERE_API_URL', config.COHERE_API_URL)
        config.COHERE_API_KEY = request.form.get('COHERE_API_KEY', config.COHERE_API_KEY)
        config.COHERE_MODEL = request.form.get('COHERE_MODEL', config.COHERE_MODEL)
        config.CHROME_DRIVER_PATH = request.form.get('CHROME_DRIVER_PATH', config.CHROME_DRIVER_PATH)
        config.OUTPUT_FILE_PATH = request.form.get('OUTPUT_FILE_PATH', config.OUTPUT_FILE_PATH)
        
        # Update config.SEARCH_ENGINES with new entries
        search_engine_names = request.form.getlist('search_engine_name[]')
        search_engine_urls = request.form.getlist('search_engine_url[]')
        config.SEARCH_ENGINES = {name: url for name, url in zip(search_engine_names, search_engine_urls) if name and url}
        
        # Save the updated configuration to the config file
        with open('config.py', 'w') as f:
            for key, value in vars(config).items():
                if not key.startswith('__'):
                    f.write(f"{key} = {repr(value)}\n")
        
        flash('Configuration updated successfully', 'success')
        return redirect(url_for('index'))
    
    return render_template('config.html', config=config)

@app.route('/process', methods=['POST'])
def process():
    query = request.form.get('query')
    languages_to_translate = request.form.getlist('languages')
    selected_models = request.form.getlist('model')
    search_engines = request.form.getlist('search_engines')
    numero_pagine = int(request.form.get('numero_pagine', 1))
    process_type = request.form.get('process_type', 'web')

    use_ollama = 'Ollama' in selected_models  
    use_cohere = 'Cohere' in selected_models
    use_gpt = 'GPT' in selected_models
    use_gemini = 'Gemini' in selected_models  # Aggiunto supporto per Gemini

    translations = translate_text(query, languages_to_translate)

    try:
        if process_type == 'web':
            scrape_and_process(
                query=query,
                translations=translations,
                numero_pagine=numero_pagine,
                use_ollama=use_ollama,
                use_cohere=use_cohere,
                use_gpt=use_gpt,
                use_gemini=use_gemini,
                search_engines=search_engines
            )
        elif process_type == 'file':
            if 'file' not in request.files or not allowed_file(request.files['file'].filename):
                flash('Invalid file type or no file selected', 'error')
                return redirect(url_for('index'))
            
            file = request.files['file']
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            scrape_and_process(
                query=query,
                translations=translations,
                use_ollama=use_ollama,
                use_cohere=use_cohere,
                use_gpt=use_gpt,
                use_gemini=use_gemini,
                process_file_path=filepath
            )
        elif process_type == 'audio':
            if 'audio_file' not in request.files or not allowed_file(request.files['audio_file'].filename):
                flash('Invalid audio file type or no audio file uploaded', 'error')
                return redirect(url_for('index'))
            
            audio_file = request.files['audio_file']
            filename = secure_filename(audio_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(filepath)
            
            scrape_and_process(
                query=query,
                translations={},
                use_ollama=use_ollama,
                use_cohere=use_cohere,
                use_gpt=use_gpt,
                use_gemini=use_gemini,
                process_audio_path=filepath
            )
        else:
            flash('Invalid process type', 'error')
            return redirect(url_for('index'))

        # Read the output from the model responses
        with open('files/model_responses.txt', 'r', encoding='utf-8') as file:
            output_content = file.read()

        ai_response = send_request_to_ai(
            prompt=query + "::ATTENZIONE sulla base della precedente query genera un codice html, js e css che sia visualizzabile all'interno di una textarea html come se fosse uno snippett di codice, questo per visualizzare al meglio graficamente, in modo interattivo, come fosse uno snippett che si modifica in base al prompt, una mappa, un grafico o qualunque cosa che meglio descriva la query e i dati, grazie mille, ovviamentre non darlo così '```html' altrimenti non si può visualizzare correttamente, deve essere uno snippet di html che viene visualizzato come se fosse uno snippet e quindi non in formato codice ma di pagina, capito, non scrivere nemmeno testo altyriemntio si visualizza il testo, se decidi di creare un grafico fornisci solo html, css e js per fgare il grafico e nulla di più, non serve partire dal tag html poichè sei già al suo interno dati::" + output_content,
            use_ollama=use_ollama,
            use_cohere=use_cohere,
            use_gpt=use_gpt,
            use_gemini=use_gemini  # Aggiunto supporto per Gemini
        ).removeprefix("GPT: ```html").removesuffix("```")

        # List specific .txt files based on process_type
        if process_type == 'audio':
            text_files = ['model_responses.txt', 'scraped_texts.txt']
        elif process_type == 'file':
            text_files = ['final_summary.txt', 'page_summaries.txt', 'scraped_texts.txt']
        else:  # web
            text_files = ['model_output_file_no_link.txt', 'scraped_texts.txt', 'model_responses.txt']
        
        # Filter the list to include only existing files
        text_files = [f for f in text_files if os.path.exists(os.path.join('files/', f))]
        
    except FileNotFoundError:
        logging.error(f"Output file not found: model_responses.txt")
        flash('Output file not found. Please try again.', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logging.exception("Error during processing")
        flash(f'Error during processing: {str(e)}', 'error')
        return redirect(url_for('index'))

    return render_template(
        'process_result.html',
        query=query,
        translations=translations,
        output=output_content,
        ai_response=ai_response,
        text_files=text_files,
        get_file_preview=get_file_preview,
        current_year=datetime.now().year
    )

def get_file_preview(filename, max_length=100):
    try:
        with open('files/'+filename, 'r', encoding='utf-8') as file:
            content = file.read(max_length)  # Read only the first max_length characters
            return content.replace('\n', ' ')  # Replace newlines with spaces for better formatting
    except Exception:
        return "Could not preview file."

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory('files/', filename, as_attachment=True)

@app.route('/discussion', methods=['GET', 'POST'])
def discussion_page():
    if request.method == 'POST':
        # Fetch form data
        input_source = request.form.get('input_source')
        query = request.form.get('query') or ""  # Inizializziamo la query come stringa vuota se non esiste
        cycles = int(request.form.get('cycles'))
        chatbots = request.form.getlist('chatbots')
        summary_bot = request.form.get('summary_bot')
        uploaded_file = request.files.get('file')

        # Handle file upload if present
        if uploaded_file:
            file_content = uploaded_file.read().decode('utf-8')  # assuming text files
            query += "\n" + file_content  # Concatenare il contenuto del file alla query
        
        # Creiamo una lista di istanze di chatbot
        chatbot_instances = [{'type': bot} for bot in chatbots]
        
        # Import and invoke chatbot discussion function
        from chatbot_discussion import conduct_discussion, generate_summary
        conversation_history = conduct_discussion(query, chatbot_instances, cycles)
        summary = generate_summary(conversation_history, {'type': summary_bot})
        
        # Pass results to the HTML template for display
        return render_template('chatbot_discussion.html', summary=summary, conversation=conversation_history)
    
    # On GET request, render the discussion page
    return render_template('chatbot_discussion.html')

if __name__ == '__main__':
    app.run(debug=True)
