# Copyright 2022 PAL Authors. All rights reserved.
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

import io
import re
import signal
from contextlib import redirect_stdout
from typing import Any, Callable

from pal.core.runtime import GenericRuntime
from pal.core.backend import call_api


class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def timeout_handler(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.timeout_handler)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)
        
        
class Interface:
    def __init__(
        self,
        system_message: str,
        verbose: bool = False
    ) -> None:
        self.history = []
        self.system_message = system_message
        self.verbose = verbose
    
    def clear_history(self):
        self.history = []
        
    def generate(self, prompt: str, **kwargs):
        messages = [
            {'role': 'system', 'content': self.system_message}, 
            {'role': 'user', 'content': prompt}
        ]
        response = call_api(messages=messages, **kwargs)
        ans = response.choices[0].message.content
        if self.verbose:
            print(ans)
        self.history += [ans]
        return ans


#%%
def extract_answer(response: str | None) -> Any:
    if response is None:
        return None
    
    ANS_PATTERN = r'(?<=The answer is )\w+(?=\.)'
    ans = re.findall(ANS_PATTERN, response) or re.findall(r'\d+', response)
    
    if ans:
        return ans[-1]
    
    print('WARN: No answer found in the response.')
    return response


class TextInterface(Interface):
    def __init__(
        self,
        system_message: str,
        verbose: bool = False,
        extract_answer_fn: Callable[[str], Any] | None = None,
    ):
        super().__init__(system_message=system_message, verbose=verbose)
        self.extract_answer_fn = extract_answer_fn
    
    def run(self, prompt: str, **kwargs):
        ans = self.generate(prompt, **kwargs)
        if self.extract_answer_fn:
            return self.extract_answer_fn(ans)
        return extract_answer(ans)


#%%
def extract_code(ans: str | None) -> list[str]:
    if ans is None:
        return []
    
    # see https://stackoverflow.com/questions/76269934
    MD_CODE_PATTERN = r'^```(?:\w+)?\s*\n(.*?)(?=^```)```'
    code_block: list[str] = re.findall(MD_CODE_PATTERN, ans, re.DOTALL | re.MULTILINE)

    if code_block:
        return code_block[0].split('\n')

    print('WARN: No code block found in the answer.')
    return ans.split('\n')


class ProgramChatInterface(Interface):
    def __init__(self, 
                 system_message: str, 
                 verbose: bool = False,
                 runtime: GenericRuntime | None = None,
                 get_answer_varname: str | None = None,
                 get_answer_expr: str | None = None,
                 get_answer_from_stdout: bool = False,
                 **kwargs):
        super().__init__(system_message=system_message,
                         verbose=verbose, 
                         **kwargs)
        
        self.runtime = runtime or GenericRuntime()
        self.answer_varname = get_answer_varname
        self.answer_expr = get_answer_expr
        self.get_answer_from_stdout = get_answer_from_stdout

    def run(self, prompt: str, time_out: float = 10, **kwargs):
        ans = self.generate(prompt, **kwargs)
        code = extract_code(ans)
        with timeout(time_out):
            try:
                exec_result = self.execute(code)
            except Exception as e:
                print(e)
        return exec_result
    
    def execute(self, code: list[str] | None = None):
        code = code or []
        if self.get_answer_from_stdout:
            program_io = io.StringIO()
            with redirect_stdout(program_io):
                self.runtime.exec_code('\n'.join(code))
            program_io.seek(0)
            return program_io.readlines()[-1]
        elif self.answer_varname:
            self.runtime.exec_code('\n'.join(code))
            return self.runtime._global_vars[self.answer_varname]
        elif self.answer_expr:
            self.runtime.exec_code('\n'.join(code))
            return self.runtime.eval_code(self.answer_expr)
        else:
            self.runtime.exec_code('\n'.join(code[:-1]))
            return self.runtime.eval_code(code[-1])
    

# %%
if __name__ == '__main__':
    from pal.prompt import COT_PROMPT, DIRECT_PROMPT
    print(extract_answer(COT_PROMPT))
    print(extract_answer(DIRECT_PROMPT))
