import ollama
# THIS FUNCTION WILL BE REQUESTED BY THE MAIN PROGRAM. DO NOT DELETE
def generate_response(file,model='llava'):
    print(f'Generating info for file {file}')
    res = ollama.chat(
        model=model,
        messages=[
            {
                'role': 'user',
                'content': 'Please identify the objects in the photo provided. Please make sure to keep the response under 50 words (create a summary.)',
                'images': file
            }
        ]
    )
    print(f'Response Generated {res['message']['content']}')

    return str(res['message']['content'])   
