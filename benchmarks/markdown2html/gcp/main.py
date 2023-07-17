import markdown
import base64


def handler(request):
    request_json = request.get_json(silent=True)
    try:
        text = request_json["markdown"]
    except:
        return {"Error": "Possibly lacking markdown parameter in request."}

    decoded_text = base64.b64decode(text.encode()).decode()

    html = markdown.markdown(decoded_text)

    return {"html_response": html}
