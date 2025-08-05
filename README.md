# testAsite

## How to use
1. Install Poetry if you need.  
https://python-poetry.org/docs/
```
curl -sSL https://install.python-poetry.org | python3 -
```
2. Modify urllist.txt

3. Execute script
- Poetry
```
poetry install
poetry run python urltest.py
```
- Python
```
pip install -r requirements.txt
python urltest.py
```

4. Login to testAsite after chrome opened and connected to authentication page.

5. After login and completed script tasks, result.csv file will be created to current directory.