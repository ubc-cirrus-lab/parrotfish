import markdown

def lambda_handler(event, context):
    try:
        text = event["markdown"]
    except:
        return {'Error' : 'Possibly lacking markdown parameter in request.'}

    html = markdown.markdown(text)

    return {"html_response": html}
