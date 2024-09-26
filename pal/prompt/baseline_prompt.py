DIRECT_SYSTEM_MESSAGE = 'You will solve math problems. You will only give a direct answer.'

DIRECT_PROMPT = """
Q: Olivia has $23. She bought five bagels for $3 each. How much money does she have left?
A: The answer is 8.

Q: Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?
A: The answer is 33.

Q: There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?
A: The answer is 29.

Q: {question}
A: 
"""

COT_SYSTEM_MESSAGE = 'You will solve math problems. You will think step by step.'

COT_PROMPT = """
Q: Olivia has $23. She bought five bagels for $3 each. How much money does she have left? Let's think step by step.
A: Olivia started with $23. Five bagels of $3 each is $15. 23-15=8. The answer is 8.

Q: Michael had 58 golf balls. On tuesday, he lost 23 golf balls. On wednesday, he lost 2 more. How many golf balls did he have at the end of wednesday?
A: Michael started with 58 golf balls. He lost 23+2=25 before wednesday. 58-25=33. The answer is 33.

Q: There were nine computers in the server room. Five more computers were installed each day, from monday to thursday. How many computers are now in the server room?
A: It started with nine computers. Five computers from monday to thursday is 20. 9+20=29. The answer is 29.

Q: {question} Let's think step by step.
A: 
"""