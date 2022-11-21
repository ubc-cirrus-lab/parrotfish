import markdown
import base64


def lambda_handler(event, context):
    try:
        text = event["markdown"]
    except:
        return {'Error': 'Possibly lacking markdown parameter in request.'}

    decoded_text = base64.b64decode(text.encode()).decode()

    html = markdown.markdown(decoded_text)

    return {"html_response": html}
