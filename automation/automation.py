from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

PAPER_YEAR_PATTERN = '![Year](https://img.shields.io/badge/{}-blue?style=flat)'
PAPER_TAGS_PATTERN = '![Tags](https://img.shields.io/badge/{}-grey?style=flat)'
PAPER_AUTHOR_PATTERN = '![Tags](https://img.shields.io/badge/{}-green?style=flat)'
PAPER_PATH_PATTERN = '[![file](https://img.shields.io/badge/Paper-red?style=flat)]({})'
AUTOGENERATED_TOKEN = {
    'DOX': '<!-- AUTOGENERATED_DOX -->',
    'FL': '<!-- AUTOGENERATED_FL -->',
    'KG': '<!-- AUTOGENERATED_KG -->',
    'ML': '<!-- AUTOGENERATED_ML -->',
    'NLP': '<!-- AUTOGENERATED_NLP -->',
    'TAB': '<!-- AUTOGENERATED_TAB -->'
}


def update_database(file_path: str, data_path: str, topics: List[str], columns: List[str]) -> pd.DataFrame:
    database = pd.read_csv(data_path)
    paper_df = pd.DataFrame(columns=columns)

    for topic in topics:
        paper_paths = Path(file_path + topic).glob('*.pdf')

        paper_list = []
        for paper_path in paper_paths:
            paper_list.append(str(paper_path))
        paper_list.sort()

        for paper in paper_list:
            topic = paper.split('/')[1]
            file_name = paper.split('/')[-1][:-4]
            year = file_name[1:5]
            tag = file_name.split('@')[-1].split(' ')[0] if '@' in file_name else ''
            author = file_name.split(']')[0].split(' ')[-1]
            title = file_name.split('] ')[1].split('.pdf')[0]
            row = pd.DataFrame([[topic, year, tag, author, title, paper, '']], columns=columns)
            if row['title'].values not in database['title'].values:
                paper_df = pd.concat([paper_df, row], ignore_index=True)
                print(row)
    print(f'extracted {len(paper_df)} papers')

    database = pd.concat([database, paper_df], ignore_index=True)
    database = database.sort_values('path', ignore_index=True)
    database.to_csv(data_path, index=False)

    return database


def load_table_entries(path: str, topic: str) -> List[str]:
    df = pd.read_csv(path, dtype=str)
    df = df[df['topic'] == topic]
    df.columns = df.columns.str.strip()
    return [format_entry(row) for _, row in df.iterrows()]


def format_entry(entry: pd.Series) -> str:
    title = entry.loc['title'].replace('_', ': ')
    year = entry.loc['year']
    year = PAPER_YEAR_PATTERN.format(year)
    tags = entry.loc['tags'] if isinstance(entry.loc['tags'], str) else ''
    tags = PAPER_TAGS_PATTERN.format(tags)
    author = entry.loc['author'].replace('-', '_')
    author = PAPER_AUTHOR_PATTERN.format(author)
    path = entry.loc['path'].replace(' ', '%20')
    path = PAPER_PATH_PATTERN.format(path)
    status = entry.loc['status'] if isinstance(entry.loc['status'], str) else ''
    return f'#### {status} {title}\n\n- {year}\n{tags}\n{author}\n{path}\n'


def read_lines_from_file(path: str) -> List[str]:
    '''Reads lines from file and strips trailing whitespaces.'''
    with open(path) as file:
        return [line.rstrip() for line in file]


def inject_markdown_table_into_readme(readme_lines: List[str], table_lines: List[str], topic: str) -> List[str]:
    '''Injects markdown table into readme.'''
    lines_with_token_indexes = search_lines_with_token(lines=readme_lines, token=AUTOGENERATED_TOKEN.get(topic))
    if len(lines_with_token_indexes) != 2:
        raise Exception(f'Please inject two {AUTOGENERATED_TOKEN.get("topic")} '
                        f'tokens to signal start and end of autogenerated table.')

    [table_start_line_index, table_end_line_index] = lines_with_token_indexes
    return readme_lines[:table_start_line_index + 1] + table_lines + readme_lines[table_end_line_index:]


def search_lines_with_token(lines: List[str], token: str) -> List[int]:
    '''Searches for lines with token. '''
    result = []
    for line_index, line in enumerate(lines):
        if token in line:
            result.append(line_index)
    return result


def save_lines_to_file(path: str, lines: List[str]) -> None:
    '''Saves lines to file. '''
    with open(path, 'w') as f:
        for line in lines:
            f.write('%s\n' % line)


if __name__ == '__main__':
    file_path = './files/'
    data_path = './automation/dataset.csv'
    readme_path = 'README.md'

    topics = ['DOX', 'FL', 'KG', 'ML', 'NLP', 'TAB']
    columns = ['topic', 'year', 'tags', 'author', 'title', 'path', 'status']

    update_database(file_path=file_path, data_path=data_path, topics=topics, columns=columns)

    for topic in topics:
        table_lines = load_table_entries(path=data_path, topic=topic)
        readme_lines = read_lines_from_file(path=readme_path)
        readme_lines = inject_markdown_table_into_readme(readme_lines=readme_lines,
                                                         table_lines=table_lines,
                                                         topic=topic)
        save_lines_to_file(path=readme_path, lines=readme_lines)
