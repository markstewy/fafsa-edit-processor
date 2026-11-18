"""
This module contains pure helper functions and common utilities that can be 
safely reused across multiple validation rules (e.g., string sanitization, 
type normalization, or parsing helpers).

ARCHITECTURE GUIDELINES:
- Utilities are NOT rules themselves; they contain no business logic or validation state.
- STRICTLY DISCOURAGED: Rules calling other rules. Rules must remain completely isolated 
  and independent. Allowing rules to depend on other rules creates brittle interdependencies 
  and hard-to-debug cascading changes when requirements shift. 
- Only use this file for non-rule utility helpers.
"""