# Web app for Text annotation


## Table

**Primary key:** call_id

| Column Name | Column Description |
|-------------|-------------------|
| call_id        | connectionID + chunkID |
| username         | Annotator name |
| date     | Date of annotation (YYYY-mm-dd) |
| time       | Time of annotation (HH:MM:SS) |
| case_type      | Intent selections (Comma separated values) |
| subcase_type      | Sub intent selections (Comma separated values) |
| confidence        | High, Medium or low |
| comments | Additional comments by the annotator |

---
## Reviewer table

**Primary key:** call_id, date, time

| Column Name | Column Description |
|-------------|-------------------|
| call_id        | connectionID + chunkID |
| annotator_name         | Annotator name |
| reviewer_name         | Reviewer name |
| date     | Date of annotation (YYYY-mm-dd) |
| time       | Time of annotation (HH:MM:SS) |
| case_type      | Intent selections (Comma separated values) |
| subcase_type      | Sub intent selections (Comma separated values) |
| confidence        | High, Medium or low |
| comments | Additional comments by the annotator |
