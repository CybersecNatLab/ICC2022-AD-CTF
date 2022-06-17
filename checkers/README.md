# International Cybersecurity Challenge 2022 - Athens

## Services checkers

|  #  | service                   | store | checker                           |
| :-: | :------------------------ | :---: | --------------------------------- |
|  0  | ClosedSea                 |   1   | [checker](/checkers/0/checker.py) |
|  1  | ClosedSea                 |   2   | [checker](/checkers/1/checker.py) |
|  2  | CyberUni - ExamNotes      |   1   | [checker](/checkers/2/checker.py) |
|  3  | CyberUni - EncryptedNotes |   2   | [checker](/checkers/3/checker.py) |
|  4  | CyberUni - ExamPortal     |   3   | [checker](/checkers/4/checker.py) |
|  5  | RPN                       |   1   | [checker](/checkers/5/checker.py) |
|  6  | RPN                       |   2   | [checker](/checkers/6/checker.py) |
|  7  | Trademark                 |   1   | [checker](/checkers/7/checker.py) |

## How to run

- Check sla: `ACTION=CHECK_SLA TEAM_ID=0 ROUND=0 ./checker.py`
- Put flag: `ACTION=PUT_FLAG TEAM_ID=0 ROUND=0 FLAG=FLAG ./checker.py`
- Get flag: `ACTION=GET_FLAG TEAM_ID=0 ROUND=0 FLAG=FLAG ./checker.py`
