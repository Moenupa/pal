# Copyright 2023 PAL Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import copy
import json
import argparse
import tqdm
import os

from pal import interface
from pal.prompt import (
    COT_PROMPT, COT_SYSTEM_MESSAGE,
    DIRECT_PROMPT, DIRECT_SYSTEM_MESSAGE,
    MATH_CHAT_BETA_PROMPT, MATH_CHAT_BETA_SYSTEM_MESSAGE,
    MATH_NOVAR_PROMPT
)

parser = argparse.ArgumentParser()
parser.add_argument('--append', action='store_true')
parser.add_argument('--verbose', action='store_true')
parser.add_argument('--dataset', default='gsm', type=str)
parser.add_argument('--model', default='llama-3.1-70b-versatile', type=str)
parser.add_argument('--temperature', default=0.0, type=float)
parser.add_argument('--top_p', default=1.0, type=float)
parser.add_argument('--max_tokens', default=1024, type=int)
parser.add_argument('--prompt', default='pal', type=str)
args = parser.parse_args()

DATA_PATH = f'datasets/{args.dataset}.jsonl'
OUTPUT_PATH = f'results/{args.dataset}_{args.prompt}_{args.model}.chat.jsonl'
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

examples = list(map(json.loads, open(DATA_PATH)))

if args.prompt == 'pal':
    PROMPT_FORMAT = MATH_CHAT_BETA_PROMPT
    itf = interface.ProgramChatInterface(
        get_answer_expr='solution()',
        verbose=args.verbose,
        system_message=MATH_CHAT_BETA_SYSTEM_MESSAGE,
    )
elif args.prompt == 'palvar':
    PROMPT_FORMAT = MATH_NOVAR_PROMPT
    itf = interface.ProgramChatInterface(
        get_answer_expr='solution()',
        verbose=args.verbose,
        system_message=MATH_CHAT_BETA_SYSTEM_MESSAGE,
    )
elif args.prompt == 'cot':
    PROMPT_FORMAT = COT_PROMPT
    itf = interface.TextInterface(
        verbose=args.verbose,
        system_message=COT_SYSTEM_MESSAGE,
    )
elif args.prompt == 'direct':
    PROMPT_FORMAT = DIRECT_PROMPT
    itf = interface.TextInterface(
        verbose=args.verbose,
        system_message=DIRECT_SYSTEM_MESSAGE,
    )
else:
    raise ValueError(f'Unknown prompt {args.prompt}')

if args.append:
    lines = open(OUTPUT_PATH).readlines()
    num_skip_exps = len(lines)
    scores = [x['score'] for x in map(json.loads, lines)]
else:
    num_skip_exps = 0
    scores = []

with open(OUTPUT_PATH, 'a' if args.append else 'w') as f:
    pbar = tqdm.tqdm(examples[num_skip_exps:500], initial=num_skip_exps, total=500)
    for x in pbar:
        question = x['input']
        result = copy.copy(x)
        
        try:
            ans = itf.run(
                PROMPT_FORMAT.format(question=question),
                stop=None,
                model=args.model,
                temperature=args.temperature,
                top_p=args.top_p,
                max_tokens=args.max_tokens
            )
            ans = float(ans)
            score = 1 if abs(ans - x['target']) < 1e-3 else 0
        except Exception as e:
            print(e)
            ans = ''
            score = 0
        scores.append(score)
        
        result['answer'] = ans
        result['score'] = score
        result['generation'] = itf.history
        f.write(json.dumps(result) + '\n')
        
        itf.clear_history()
        f.flush()

print(f'Accuracy - {sum(scores) / len(scores)}')
