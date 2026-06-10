# Formula Engine

Keneya Lab uses a shared safe formula engine for calculated analytes and automated validation rules.

## Syntax

Reference analytes by code with braces:

```text
{GLU}
{CREAT}
```

Calculated formulas must return a number:

```text
{CHOL} - {HDL}
round({GLU} / {CREAT}, 2)
abs({A} - {B})
```

Consistency formulas must return true or false:

```text
{GLU} / {INS} > 0.85
abs({NA} - {CL}) < 40
{A} > 5 and {B} < 10
```

## Supported Operators

Arithmetic:

```text
+  -  *  /  %  **
```

Comparisons:

```text
>  >=  <  <=  ==  !=
```

Boolean logic:

```text
and  or  not
```

Parentheses are supported.

## Supported Functions

Only these functions are allowed:

```text
abs(value)
min(a, b, ...)
max(a, b, ...)
round(value, digits)
```

The allow-list is centralized in the backend formula engine so future safe functions can be added deliberately.

## Safety Model

The engine parses formulas with Python AST and evaluates only a strict allow-list.

The engine does not allow:

- Python `eval` or `exec`
- imports
- attribute access
- indexing/subscripts
- comprehensions
- lambdas
- arbitrary function calls
- strings, objects, lists, or dictionaries inside formulas

All analyte references must exist, must not be deleted, and must be numeric-compatible for formula evaluation.

## Result Types

Calculated analytes use `number`.

Consistency rules use `boolean`.

If a formula returns the wrong type, the backend rejects it before saving.

## Decimal Display

Formula evaluation uses `Decimal` internally, but frontend-facing numeric results are rounded to exactly two decimal digits.

Examples:

```text
{A} / {B} with A = 10 and B = 3 -> 3,33
{A} - {B} with A = 10 and B = 3 -> 7,00
```

Use the shared frontend decimal formatter for displaying numeric formula results. Do not render raw formula engine decimal strings in the UI.

## Common Errors

| Error | Meaning | Fix |
| --- | --- | --- |
| `La formule est requise` | Formula is empty | Enter a formula |
| `Syntaxe de formule invalide` | The expression cannot be parsed | Check parentheses and operators |
| `Analyte inconnu dans la formule` | `{CODE}` does not match an active analyte | Insert a valid analyte reference |
| `La valeur de CODE est requise` | Preview is missing a sample value | Enter a sample value |
| `La valeur de CODE doit être numérique` | Preview value is not numeric | Use a numeric value |
| `Fonction de formule non autorisée` | Function is not in the allow-list | Use `abs`, `min`, `max`, or `round` |
| `Division par zéro ou calcul invalide` | The sample values cause an invalid calculation | Change sample values |
| `La formule doit retourner une valeur numérique` | Calculated analyte formula returned true/false | Use arithmetic formula output |
| `La formule doit retourner vrai ou faux` | Consistency formula returned a number | Add a comparison |

## Future Runtime Integration

The engine is ready to be reused by result/order workflows:

- Calculated analytes can evaluate `calculation_formula` once required source analytes are resulted.
- Consistency rules can evaluate formulas after all linked analytes for an order item have values.
- Reflex rules use a separate operator/value evaluator and can later auto-add catalog tests or panels during result entry.
