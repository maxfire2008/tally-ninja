# Specification for the RaceML format

> <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br /><span xmlns:dct="http://purl.org/dc/terms/" href="http://purl.org/dc/dcmitype/Text" property="dct:title" rel="dct:type">The RaceML format (this file - spec.md)</span> by <span xmlns:cc="http://creativecommons.org/ns#" property="cc:attributionName">Max Burgess</span> is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.
>
> :warning: This license only applies to this file, not to any other content in this repository.

## overall file structure
A RaceML database consists of a directory with the following subdirectories:
- `athletes`
- `leagues`
- `results`

## Properties of RaceML files
RaceML files may contain keys that are unsupported by the general format - these should begin with `custom_` then a package identifier using the reverse domain format, e.g. `custom_net.maxstuff.myapp_race_fee`. Although it's suggested to submit a GitHub issue requesting an addition to the format.

| key              | format                                                                    | example value    |
| ---------------- | ------------------------------------------------------------------------- | ---------------- |
| `_include`       | string, path to another file in the same directory                        | `_defaults.yaml` |
| `_template_only` | boolean, if true the file should only be used as part of the _include key | `true`           |

## Athlete file
The athlete files must have unique names (even if in different sub-directories).

Athlete file keys:
| key      | format                                                    | example value        |
| -------- | --------------------------------------------------------- | -------------------- |
| `name`   | string, any printable characters                          | `Joe Smith`          |
| `dob`    | string of date in ISO 8601 format                         | `2000-01-01`         |
| `gender` | can be anything, used only in [eligibility](#eligibility) | `male`               |
| `team`   | string, any printable characters - preferably snake_case  | `team_new_york_city` |

## League file
The league files do not need to have unique names although the path will be included as part of the filename. An athlete should only be eligible for one league of each type per results file.

League file keys:
| key            | format                                                                        | example value          |
| -------------- | ----------------------------------------------------------------------------- | ---------------------- |
| `scoring`      | a dictionary of scoring rules (see below)                                     |                        |
| `name`         | string, any printable characters                                              | `New York City League` |
| `league_type`  | string, (see below)                                                           | `team`                 |
| `permit_teams` | boolean, if true results of team events will be allowed in the league's total | `true`                 |

### Scoring rules
Each results has a `type` key which is then looked up in the scoring dictionary (this is overridden by `scoring_type`).

#### `method: minus_place`
| key                | format  | example value |
| ------------------ | ------- | ------------- |
| `method`           | string  | `minus_place` |
| `method_value`     | integer | `10`          |
| `method_decrement` | integer | `1`           |
| `sort_by`          | string  | `lowest`      |
| `sort_key`         | string  | `finish_time` |

In the above example, the athlete will receive 10 points for coming first, 9 for second, 8 for third, and 0 for 11th or lower. This is common for running events, where the person with the fastest time wins.

#### combine methods
Combine methods allow for multiple results to be combined into one score. For example, in long jump events the athlete will have multiple attempts and the best one will be used for the score.
```yaml
sort_by: 'highest'
combine_method: 'max' # gets the highest value from the results
sort_key: 'distances'
```

#### eligibility
Eligibility rules are a powerful part of RaceML. They allow for comparisons to be made between ... #TODO


### League types
| type         | description                                     |
| ------------ | ----------------------------------------------- |
| `individual` | tally points to the athlete's individual total. |
| `team`       | tally points to the athlete's team's totals.    |


## Results file
The results files do not need to have unique names although the path will be included as part of the filename.

Results file keys:
| key        | format                                        | example value                       |
| ---------- | --------------------------------------------- | ----------------------------------- |
| `type`     | a string representing the type of event       | `race`                              |
| `name`     | string, any printable characters              | `5k Race Sponsored by maxstuff.net` |
| `distance` | can be anything - for use in comparisons only | `5k`                                |
#TODO