from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from openai import OpenAI

app = FastAPI()

# CORS (SharePoint no tendrá problemas)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ===============================
# ENDPOINT DE PRUEBA
# ===============================
@app.get("/")
def root():
    return {"status": "Inventario Agent API OK"}

# ===============================
# OBTENER TOKEN GRAPH
# ===============================
def get_graph_token():
    url = f"https://login.microsoftonline.com/{os.getenv('TENANT_ID')}/oauth2/v2.0/token"

    data = {
        "client_id": os.getenv("CLIENT_ID"),
        "client_secret": os.getenv("CLIENT_SECRET"),
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# ===============================
# CHAT ENDPOINT
# ===============================
@app.post("/chat")
def chat(payload: dict):
    user_message = payload.get("message")

    # 1️⃣ Token Graph
    graph_token = get_graph_token()
    headers = {"Authorization": f"Bearer {graph_token}"}

    site_id = os.getenv("SHAREPOINT_SITE_ID")

    # 2️⃣ Leer listas SharePoint (ejemplo simple)
    lists_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists"
    lists_res = requests.get(lists_url, headers=headers)
    lists_res.raise_for_status()

    list_names = [l["displayName"] for l in lists_res.json()["value"]]

    # 3️⃣ Enviar contexto a OpenAI
    prompt = f"""
Eres un asistente experto en inventarios y auditoría.

Listas disponibles en SharePoint:
{", ".join(list_names)}

Pregunta del usuario:
{user_message}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return {
        "reply": response.choices[0].message.content
    }
