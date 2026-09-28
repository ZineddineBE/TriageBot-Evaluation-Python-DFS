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
  for key in ["category", "severity", "sentiment", "summary", "draft"]:
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
  if not isinstance(data["draft"], str) or not data["draft"].strip():
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
        data["draft"] = html.unescape(data["draft"])
        data["status"] = "processed"
        return data

      print(f"  -> Tentative {attempt + 1}/2 : format non valide")

    except ConnectionError:
      print("Erreur : Ollama n'est pas lancé.")
      sys.exit(1)
    except Exception:
      print(f"  -> Tentative {attempt + 1}/2 : erreur de réponse")

  return {
    "category": "autre",
    "severity": 3,
    "sentiment": "neutral",
    "summary": "Échec validation",
    "draft": "Bonjour, votre demande a bien été reçue et est en cours d'analyse.",
    "status": "to_check"
  }


def get_escalation(analysis: dict) -> str:
  """Règles d'escalade déterministes sans LLM."""
  status = analysis.get("status")
  category = analysis.get("category")
  severity = analysis.get("severity", 0)

  if status == "to_check":
    return "Relecture humaine obligatoire"
  if category == "toxicity":
    return "À transmettre à l'équipe modération"
  if category == "payment" and severity >= 4:
    return "À transmettre au responsable support"
  return "Traitement standard"


def show_dashboard(results: list) -> None:
  print("\n--- TABLEAU DE BORD ---")
  active = [r for r in results if r["analysis"]["status"] in ("processed", "to_check", "duplicate")]
  if not active:
    print("Aucun ticket exploitable.")
    return

  counts = {}
  for item in active:
    cat = item["analysis"]["category"]
    counts[cat] = counts.get(cat, 0) + 1

  print("\nTickets par catégorie :")
  for cat, total in sorted(counts.items()):
    print(f"- {cat} : {total}")

  severities = [item["analysis"]["severity"] for item in active]
  avg = sum(severities) / len(severities)
  print(f"\nUrgence moyenne : {avg:.1f} / 5")

  sorted_tickets = sorted(active, key=lambda x: x["analysis"]["severity"], reverse=True)
  print("\nTop 3 des urgences :")
  for item in sorted_tickets[:3]:
    t = item["ticket"]
    a = item["analysis"]
    print(f"- [Urgence {a['severity']}] #{t['id']} {t['player']} : {a['summary']}")
  print("-----------------------\n")


# ------ Script principal ------ #
def main():
  tickets_path = BASE_DIR / "tickets.json"
  output_path = BASE_DIR / "results.json"
  tickets = load_tickets(tickets_path)
  results = []
  seen = {}

  print(f"Démarrage du triage ({MODEL})...\n")

  for ticket in tickets:
    player = ticket.get("player", "").strip()
    message = ticket.get("message", "").strip()

    if not message:
      print(f"Ticket #{ticket['id']} ignoré (message vide)")
      results.append({
        "ticket": ticket,
        "analysis": {
          "category": "autre",
          "severity": 1,
          "sentiment": "neutral",
          "summary": "Message vide",
          "draft": "",
          "status": "ignored",
          "escalation": "Traitement standard"
        }
      })
      continue

    key = (player, message)
    if key in seen:
      print(f"Ticket #{ticket['id']} doublon détecté pour {player}")
      cached = dict(seen[key])
      cached["status"] = "duplicate"
      results.append({"ticket": ticket, "analysis": cached})
      continue

    print(f"Ticket #{ticket['id']} en cours ({player})...")
    analysis = analyze_ticket(ticket)
    analysis["escalation"] = get_escalation(analysis)
    seen[key] = analysis

    results.append({"ticket": ticket, "analysis": analysis})

  with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

  print(f"\nRésultats exportés dans {output_path.name}")
  show_dashboard(results)


if __name__ == "__main__":
  main()