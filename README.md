# Web app for Text annotation


## Table Schema

**Primary key:** call_id, date, time

| Column Name | Column Description |
|-------------|-------------------|
| call_id        | connectionID + chunkID |
| username         | name of the user who logged in |
| role         | annotator or reviewer |
| date     | Date of annotation (YYYY-mm-dd) |
| time       | Time of annotation (HH:MM:SS) |
| case_type      | Intent selections (Comma separated values) |
| subcase_type      | Sub intent selections (Comma separated values) |
| confidence        | High, Medium or low |
| comments | Additional comments by the annotator/reviewer |

## How to run

- Create a virtual environment
- Install all the requirements using `pip install -r requirements.txt`
- Use `streamlit run app.py` to run the app

---
## Functionalities

### Annotator Page

- the responses are un-editable. Once the annotator "Saves and Next", then they won't be able to visit that chunk again.

### Reviewer Page

- able to select a call text by connection id
- able to review annotations for the same call text as many times.


## Pending Tasks

- [x] Docstrings for functions
- [ ] Adding CSS 
- [x] Close database connection on exiting app
- [x] Add logging functionalities
- [x] Add exception handling
- [ ] Automatically scroll a little bit up when the user clicks the buttons.
 