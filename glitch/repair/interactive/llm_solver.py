from ollama import chat # type: ignore
from ollama import ChatResponse
from glitch.repair.interactive.system import SystemState
from glitch.tech import Tech

class PatchSolver:
    def __init__(
        self,
        script: str,
        filesystem: SystemState,
        tech: Tech
    ) -> None:
        self.script = script
        self.filesystem = filesystem
        self.tech = tech

    def solve(self) -> str | None:
        response: ChatResponse = chat(model='deepseek-r1:8b', messages=[
            {
                'role': 'user',
                'content': f'''
Consider the following Chef code snippet:
{self.script}

Consider also the following specification:
{str(self.filesystem.state)}
The specification defines the attributes for each resource.
For instance, the specification {{ "a": {{"mode": "0777" }} }} means that the attribute 'mode' of resource 'a' should be set to '0777'.
'glitch-undef' is a special word in the specification that represents an undefined value.
If an attribute is set to 'glitch-undef', it means that the attribute is not defined and should be removed.
'glitch-undef' has no special meaning in the Chef code snippet.
DO NOT WRITE 'glitch-undef' IN YOUR SOLUTION FOR ANY REASON.
IF 'glitch-undef' IS PRESENT IN THE SPECIFICATION, IT MEANS THAT THE ATTRIBUTE SHOULD BE REMOVED.

Please fix the code snippet to satisfy the specification.
Your response SHOULD ONLY INCLUDE the fixed code snippet in the following format:
=== BEGIN SOLUTION ===
<fixed code snippet>
=== END SOLUTION ===
DO NOT INCLUDE ANYTHING ELSE IN YOUR RESPONSE.
''',
            },
        ])
        return response.message.content