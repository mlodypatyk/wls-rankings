from events import event_names, event_order
import requests
from collections import defaultdict
from rounds import round_weights

API_URL = 'https://www.worldcubeassociation.org/api/v0/competitions/'
CSV_URL = 'https://drive.google.com/uc?id=1uQLMSjPEovDWOgdCUAc9lQttcmVVXkUo'
AVERAGE_FORMATS = ['a', 'm']
KINCH_CONSTANT = 10000


def create_markdown_table(headers, data):
    final_text = ''
    final_text += '|'
    final_text += '|'.join(headers)
    final_text += '|\n|'
    final_text += '|'.join(['--']*len(headers))
    final_text += '|\n'
    for row in data:
        row_str = map(str, row)
        final_text += '|'
        final_text += '|'.join(row_str)
        final_text += '|\n'

    return final_text
        
    

def get_competition_kinch(comp_id: str):
    
    url = API_URL + comp_id + '/results'
    results = requests.get(url).json()

    people = {}
    for result in results:
        people[result['wca_id']] = result['name']

    rounds = defaultdict(set)
    for result in results:
        rounds[result['event_id']].add((result['round_id'], result['round_type_id']))
    
    winning_results = {}
    for result in results:
        if result['pos'] == 1:
            if result['format_id'] in AVERAGE_FORMATS:
                winning_results[result['round_id']] = result['average']
            else:
                winning_results[result['round_id']] = result['best']

    kinch_table = {}
    # go event by event
    for event in rounds:
        kinch_table[event] = {}
        # go round by round, from the start
        event_rounds = list(rounds[event])
        event_rounds.sort(key=lambda x: round_weights[x[1]])
        per_round_kinch = []

        for round_id, _ in event_rounds:
            this_round_kinch = []
            for result in results:
                if result['round_id'] == round_id:
                    this_result = result['average'] if result['format_id'] in AVERAGE_FORMATS else result['best']
                    this_kinch = winning_results[round_id] / this_result if this_result > 0 else 0
                    this_kinch = round(this_kinch, 4)
                    this_round_kinch.append((this_kinch, result['wca_id']))
            this_round_kinch.sort()
            per_round_kinch.append(this_round_kinch)

        for pos, round_kinch in enumerate(per_round_kinch):
            this_round_persons = [person for _, person in round_kinch]
            if pos != 0:
                prev_kinch = per_round_kinch[pos-1]
                prev_kinch_our_people = [(kinch, person) for (kinch, person) in prev_kinch if person in this_round_persons]
                smallest_kinch_person = prev_kinch_our_people[0][1]
                smallest_kinch = kinch_table[event][smallest_kinch_person]
            else:
                smallest_kinch = 0
            next_rounds_persons = []
            if pos != len(per_round_kinch) - 1:
                next_rounds_persons = [person for _, person in per_round_kinch[pos+1]]
            first_person_proceed = False
            first_person_proceed_kinch = None
            for kinch, person_id in round_kinch:
                kinch_table[event][person_id] = smallest_kinch + (1-smallest_kinch) * kinch
                if person_id in next_rounds_persons and not first_person_proceed:
                    first_person_proceed = True
                    first_person_proceed_kinch = smallest_kinch + (1-smallest_kinch) * kinch
                if person_id not in next_rounds_persons and first_person_proceed:
                    # people who quit
                    print(f'Quit {person_id}, {event}')
                    kinch_table[event][person_id] = first_person_proceed_kinch


        # Normalize the kinch
        #max_kinch = max(kinch_table[event].values())
        for person_id in kinch_table[event]:
            kinch = kinch_table[event][person_id]
            new_kinch = round(kinch * KINCH_CONSTANT, 2)
            kinch_table[event][person_id] = new_kinch
        
        # fill out the dict with people who didnt do the event
        for person_id in people:
            if person_id not in kinch_table[event]:
                kinch_table[event][person_id] = 0
        

    # add up all the events
    final_kinch = []
    events_held = [event for event in event_order if event in rounds.keys()]
    for person_id in people:
        kinches = []
        for event in events_held:
            kinches.append(kinch_table[event][person_id])
        sum_kinch = round(sum(kinches) / len(kinches))
        final_kinch.append((sum_kinch, person_id, kinches))
    final_kinch.sort(reverse=True)
    kinch_readable = []
    for sum_kinch, person_id, kinches in final_kinch:
        person_link = f'[{people[person_id]}](https://worldcubeassociation.org/persons/{person_id})'
        headers = [person_link, sum_kinch] + kinches
        kinch_readable.append(headers)

    return (people, events_held, kinch_readable, final_kinch)
        

def get_series_kinch(series_ids, eligible_ids = None):
    total_kinch = defaultdict(dict)
    all_people = {}
    for competition_id in series_ids:
        people, _, _, comp_kinch = get_competition_kinch(competition_id)
        all_people.update(people)
        for kinch, person_id, *_ in comp_kinch:
            total_kinch[person_id][competition_id] = kinch
    for person in all_people:
        for competition_id in series_ids:
            if competition_id not in total_kinch[person]:
                total_kinch[person][competition_id] = 0
    
    people_kinch_list = []
    for person in total_kinch:
        person_kinches = []
        for competition_id in series_ids:
            person_kinches.append(total_kinch[person][competition_id])
        people_kinch_list.append((sum(person_kinches), person, person_kinches))
    people_kinch_list.sort(reverse=True)

    readable_list = []
    for kinch, person, events in people_kinch_list:
        person_link = f'[{all_people[person]}](https://worldcubeassociation.org/persons/{person})'
        row = [person_link, kinch] + events
        if eligible_ids:
            if person not in eligible_ids:
                continue
        readable_list.append(row)
    return (series_ids, readable_list)


def get_ids_from_url(url):
    r = requests.get(url)
    ids_with_empty = r.text.split('\n')
    ids_final = [id for id in ids_with_empty if id]
    return ids_final
    


if __name__ == '__main__':

    series_ids = ['WLSStyczen2026']

    wls_ids = get_ids_from_url(CSV_URL)

    print(wls_ids)
    
    comps, kinch = get_series_kinch(series_ids, eligible_ids=wls_ids)
    headers = ["Person", "Kinch"] + comps
    table = create_markdown_table(headers, kinch)
    with open('test.md', 'w', encoding='utf-8') as file:
        file.write('# Rankings\n\n')
        file.write(table)
    

