import requests
import os
from datetime import datetime, timedelta

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']

EQUIPES = [
    {'id': '2025_3355_SEM_1', 'nom': 'Senior 1'},
    {'id': '2025_3355_SEM_9', 'nom': 'Senior 2'},
]

headers_supabase = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'resolution=merge-duplicates'
}

headers_fff = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://epreuves.fff.fr/',
    'Origin': 'https://epreuves.fff.fr'
}

def fetch_matches(equipe_id, date_debut, date_fin):
    url = f'https://epreuves.fff.fr/api/data/matches'
    params = {
        'dateDebut': date_debut,
        'dateFin': date_fin,
        'idEquipe': equipe_id,
        'itemsPerPage': 20,
        'pagination': 'true'
    }
    r = requests.get(url, params=params, headers=headers_fff)
    if r.status_code == 200:
        return r.json().get('hydra:member', [])
    print(f'Erreur FFF {r.status_code} pour {equipe_id}')
    return []

def save_matches(matches, equipe_id):
    rows = []
    for m in matches:
        rows.append({
            'id': str(m.get('id', '')),
            'equipe_id': equipe_id,
            'date_match': m.get('dateDebut'),
            'competition': m.get('competition', {}).get('nom', '') if m.get('competition') else '',
            'equipe_domicile': m.get('equipeLocale', {}).get('nom', '') if m.get('equipeLocale') else '',
            'equipe_exterieur': m.get('equipeVisiteuse', {}).get('nom', '') if m.get('equipeVisiteuse') else '',
            'score_domicile': m.get('scoreLocaux'),
            'score_exterieur': m.get('scoreVisiteurs'),
            'est_domicile': '508864' in str(m.get('equipeLocale', {}).get('@id', '')),
            'statut': m.get('statut', ''),
            'updated_at': datetime.utcnow().isoformat()
        })
    if not rows:
        return
    r = requests.post(
        f'{SUPABASE_URL}/rest/v1/matchs',
        json=rows,
        headers=headers_supabase
    )
    print(f'Sauvegarde {len(rows)} matchs : {r.status_code}')

def main():
    now = datetime.utcnow()
    for equipe in EQUIPES:
        print(f'Traitement {equipe["nom"]}...')
        for i in range(8):
            d = now - timedelta(days=30 * i)
            debut = f'{d.year}-{str(d.month).zfill(2)}-01T00:00:00+00:00'
            if d.month == 12:
                fin = f'{d.year}-12-31T00:00:00+00:00'
            else:
                fin_d = datetime(d.year, d.month + 1, 1) - timedelta(days=1)
                fin = f'{fin_d.year}-{str(fin_d.month).zfill(2)}-{str(fin_d.day).zfill(2)}T00:00:00+00:00'
            matches = fetch_matches(equipe['id'], debut, fin)
            save_matches(matches, equipe['id'])

if __name__ == '__main__':
    main()
