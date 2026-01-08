from senado_camara_tools import AVAILABLE_TOOLS

def handler(request):
    return {
        "statusCode": 200,
        "body": {
            "status": "ok",
            "tools_available": len(AVAILABLE_TOOLS),
            "tools_list": list(AVAILABLE_TOOLS.keys())
        }
    }