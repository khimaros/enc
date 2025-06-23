# HACKING

without making the code cryptic, prefer to reduce the total line count.
remove dead code and unnecessary or obvious comments.

maintain existing code style such as variable naming,
comment formatting, output formatting, whitespace, and quoting.

code comments and command line output should be all lowercase,
though CAPS can be used for acronyms or for emphasis.

in general, comments should focus on "why" instead of "what".
a single comment per function describing its purpose is adequate.

- avoid comments explaining what each expression is doing
- avoid "changelog" style comments describing the current code change
- remove dead code rather than commenting it out

keep dependencies to a minimum.

keep the code "DRY" and organized into small functions.
ideally, keep functions to fewer than 50 lines.
use pure functions without side effects whenever possible.
