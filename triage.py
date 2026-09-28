import html
import json
import os
import sys
from pathlib import Path
import ollama

# ------ Config générale ------ #
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
BASE_DIR = Path(__file__).parent

CATEGORIES = ["bug", "payment", "account", "suggestion", "toxicity", "autre"]
SENTIMENTS = ["positive", "neutral", "negative"]

with open(BASE_DIR / "system_prompt.txt", "r", encoding="utf-8") as prompt_file:
  SYSTEM_PROMPT = prompt_file.read()

# ------ Fonctions ------ #
def load_tickets(filepath: Path) -> list:
  if not filepath.exists():
    print(f"Erreur : le fichier '{filepath.name}' est introuvable.")
    sys.exit(1)
  try:
    with open(filepath, "r", encoding="utf-8") as f:
      return json.load(f)
  except json.JSONDecodeError:
    print(f"Erreur : le fichier '{filepath.name}' contient un JSON mal formé.")
    sys.exit(1)

def is_valid(data: dict) -> bool:
  for key in ["category", "severity", "sentiment", "summary"]:
    if key not in data:
      return False
  if data["category"] not in CATEGORIES:
    return False
  if not isinstance(data["severity"], int) or not (1 <= data["severity"] <= 5):
    return False
  if data["sentiment"] not in SENTIMENTS:
    return False
  if not isinstance(data["summary"], str) or not data["summary"].strip():
    return False
  return True

def analyze_ticket(ticket: dict) -> dict:
  prompt = f"Joueur: {ticket['player']}\nMessage: {ticket['message']}"
  for attempt in range(2):
    try:
      response = ollama.chat(
        model=MODEL,
        messages=[
          {"role": "system", "content": SYSTEM_PROMPT},
          {"role": "user", "content": prompt}
        ],
        format="json"
      )
      data = json.loads(response["message"]["content"])
      if is_valid(data):
        data["summary"] = html.unescape(data["summary"])
        data["status"] = "processed"
        return data
      print(f"  -> Tentative {attempt + 1}/2 : format non valide")
    except ConnectionError:
      print("Erreur : Ollama n'est pas lancé.")
      sys.exit(1)
    except Exception:
      print(f"  -> Tentative {attempt + 1}/2 : erreur de réponse")

  return {
    "category": "autre", "severity": 3, "sentiment": "neutral", 
    "summary": "Échec validation", "status": "to_check"
  }

# ------ Script principal ------ #
def main():
  tickets_path = BASE_DIR / "tickets.json"
  output_path = BASE_DIR / "results.json"
  tickets = load_tickets(tickets_path)
  results = []

  print(f"Démarrage du triage ({MODEL})...\n")
  for ticket in tickets:
    print(f"Ticket #{ticket['id']} en cours...")
    analysis = analyze_ticket(ticket)
    results.append({"ticket": ticket, "analysis": analysis})

  with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
  main()