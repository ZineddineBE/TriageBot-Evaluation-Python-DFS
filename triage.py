import json
import os
from pathlib import Path
import ollama

MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
BASE_DIR = Path(__file__).parent
with open(BASE_DIR / "system_prompt.txt", "r", encoding="utf-8") as prompt_file:
  SYSTEM_PROMPT = prompt_file.read()

def load_tickets(filepath: Path) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def analyze_ticket(ticket: dict) -> dict:
    prompt = f"Joueur: {ticket['player']}\nMessage: {ticket['message']}"
    
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        format="json"
    )
    
    return json.loads(response["message"]["content"])

def main():
    base_dir = Path(__file__).parent
    tickets_path = base_dir / "tickets.json"
    output_path = base_dir / "results.json"

    print("Chargement des tickets...")
    tickets = load_tickets(tickets_path)

    results = []
    for ticket in tickets:
        print(f"Analyse du ticket #{ticket['id']}...")
        analysis = analyze_ticket(ticket)
        results.append({
            "ticket": ticket,
            "analysis": analysis
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Terminé ! Résultats sauvegardés dans {output_path.name}")

if __name__ == "__main__":
    main()